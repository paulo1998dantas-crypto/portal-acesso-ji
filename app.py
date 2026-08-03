"""Portal central de acesso aos módulos operacionais da JI Montadora.

O Portal valida a mesma tabela pública de usuários já usada pelos módulos.
Ele não compartilha cookies entre domínios: após o login emite apenas um
comprovante assinado, de curtíssima duração e restrito ao módulo escolhido.
Cada aplicação valida novamente o usuário antes de abrir sua própria sessão.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
from psycopg.rows import dict_row
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash


BASE_DIR = Path(__file__).resolve().parent
MODULES = {
    "CADASTRO": {
        "name": "Módulo Cadastros",
        "label": "Base operacional",
        "number": "01",
        "card": "card-cadastros",
        "base_url": "https://modulocadastro.onrender.com",
        "default_path": "/",
    },
    "ESTOQUE": {
        "name": "Módulo Estoque",
        "label": "Almoxarifado",
        "number": "02",
        "card": "card-estoque",
        "base_url": "https://moduloestoque-cni2.onrender.com",
        "default_path": "/dashboard",
    },
    "SUPRIMENTOS": {
        "name": "Módulo Compras",
        "label": "Suprimentos",
        "number": "03",
        "card": "card-compras",
        "base_url": "https://modulo-suprimentos.onrender.com",
        "default_path": "/erp/ordens-compra",
    },
    "PCP": {
        "name": "Módulo PCP",
        "label": "Planejamento",
        "number": "04",
        "card": "card-pcp",
        "target_app": "SUPRIMENTOS",
        "base_url": "https://modulo-suprimentos.onrender.com",
        "default_path": "/erp/gestao-os",
    },
    "PRODUCAO": {
        "name": "Controle de Produção",
        "label": "Acompanhamento",
        "number": "05",
        "card": "card-producao",
        "target_app": "MES",
        "base_url": "https://projeto-final-main.onrender.com",
        "default_path": "/gestao-os",
    },
    "MES": {
        "name": "Módulo MES",
        "label": "Execução industrial",
        "number": "06",
        "card": "card-mes",
        "base_url": "https://projeto-final-main.onrender.com",
        "default_path": "/?visao=geral",
    },
}


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "sim", "on"}


def _database_url() -> str:
    value = os.environ.get("DATABASE_URL", "").strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://"):]
    return value


app = Flask(__name__, static_folder=None)
app.config.update(
    # Sem a variável o processo continua iniciando para expor /healthz, mas
    # gera uma sessão efêmera; o deploy operacional deve sempre configurá-la.
    SECRET_KEY=os.environ.get("PORTAL_SESSION_SECRET") or os.urandom(32),
    SESSION_COOKIE_NAME="ji_portal_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=_env_flag("PORTAL_COOKIE_SECURE", True),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)


def _safe_path(value: str | None, fallback: str) -> str:
    candidate = str(value or "").strip()
    parsed = urlsplit(candidate)
    if (
        not candidate.startswith("/")
        or candidate.startswith("//")
        or parsed.scheme
        or parsed.netloc
    ):
        return fallback
    return candidate


def _module(code: str):
    item = MODULES.get(str(code or "").upper())
    if not item:
        abort(404)
    return item


def _load_user(username: str):
    database_url = _database_url()
    if not database_url:
        raise RuntimeError("O Portal ainda não possui DATABASE_URL configurada.")
    with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=8) as conn:
        return conn.execute(
            """
            select id, username, password_hash, active, auth_version
              from public.users
             where lower(username) = lower(%s)
             limit 1
            """,
            (username,),
        ).fetchone()


def _revalidate_session() -> bool:
    user_id = session.get("uid")
    username = session.get("username")
    auth_version = session.get("auth_version")
    if not user_id or not username or auth_version is None:
        return False
    database_url = _database_url()
    if not database_url:
        return False
    try:
        with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=5) as conn:
            row = conn.execute(
                "select id, username, active, auth_version from public.users where id = %s limit 1",
                (int(user_id),),
            ).fetchone()
        return bool(
            row
            and row["active"]
            and row["username"].casefold() == str(username).casefold()
            and int(row.get("auth_version") or 1) == int(auth_version)
        )
    except (psycopg.Error, ValueError):
        return False


def _current_user():
    if _revalidate_session():
        return {"id": session["uid"], "username": session["username"]}
    session.clear()
    return None


def _issue_ticket(app_code: str, next_path: str) -> str:
    secret = os.environ.get("ERP_PORTAL_SSO_SECRET", "").encode("utf-8")
    if not secret:
        raise RuntimeError("A chave de integração central ainda não está configurada.")
    now = int(time.time())
    target = _module(app_code)
    payload = {
        "app": target.get("target_app", app_code),
        "uid": int(session["uid"]),
        "username": str(session["username"]),
        "auth_version": int(session["auth_version"]),
        "next": next_path,
        "iat": now,
        "exp": now + 90,
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).decode("ascii").rstrip("=")
    signature = hmac.new(secret, encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


@app.after_request
def security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "ji-portal-operacional"}


@app.get("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(BASE_DIR / "assets", filename)


@app.get("/styles.css")
def styles():
    return send_from_directory(BASE_DIR, "styles.css")


@app.get("/")
def index():
    return render_template("index.html", user=_current_user(), modules=MODULES)


@app.route("/login", methods=["GET", "POST"])
def login():
    app_code = str(request.values.get("app") or "").upper()
    module = _module(app_code) if app_code else None
    next_path = _safe_path(
        request.values.get("next"), module["default_path"] if module else "/"
    )
    if _current_user():
        if app_code:
            return redirect(url_for("open_module", app_code=app_code, next=next_path))
        return redirect(url_for("index", _anchor="modulos"))
    if request.method == "POST":
        username = str(request.form.get("username") or "").strip()
        password = str(request.form.get("password") or "")
        try:
            row = _load_user(username)
        except RuntimeError as exc:
            flash(str(exc), "error")
        except psycopg.Error:
            app.logger.exception("Falha de conexão durante o login central")
            flash("Não foi possível validar o acesso agora. Tente novamente.", "error")
        else:
            if not row or not row["active"] or not check_password_hash(row["password_hash"], password):
                flash("Usuário ou senha inválidos.", "error")
            else:
                session.clear()
                session.permanent = True
                session["uid"] = int(row["id"])
                session["username"] = str(row["username"])
                session["auth_version"] = int(row.get("auth_version") or 1)
                if app_code:
                    return redirect(url_for("open_module", app_code=app_code, next=next_path))
                return redirect(url_for("index", _anchor="modulos"))
    return render_template("login.html", module=module, app_code=app_code, next_path=next_path)


@app.get("/abrir/<app_code>")
def open_module(app_code):
    module = _module(app_code)
    target_path = _safe_path(request.args.get("next"), module["default_path"])
    if not _current_user():
        return redirect(url_for("login", app=app_code, next=target_path))
    try:
        ticket = _issue_ticket(app_code.upper(), target_path)
    except RuntimeError as exc:
        app.logger.error("SSO central não configurado: %s", exc)
        return render_template("login.html", module=module, app_code=app_code, next_path=target_path, setup_error=str(exc)), 503
    return redirect(f"{module['base_url']}/_sso/consume?ticket={ticket}", code=303)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index", _anchor="modulos"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "18080")))
