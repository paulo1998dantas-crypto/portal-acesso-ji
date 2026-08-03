# Portal Operacional — JI Montadora

Portal central de acesso aos módulos operacionais. Ele valida a mesma tabela de
usuários usada pelos módulos e encaminha o usuário para a tela solicitada sem
compartilhar cookies entre domínios Render. Cada módulo ainda valida o usuário e
mantém as próprias permissões antes de criar sua sessão local.

O login central é ativado somente com `ERP_PORTAL_SSO_ENABLED=1` nos módulos.
Enquanto a variável estiver ausente ou com valor `0`, os logins atuais de cada
aplicação continuam funcionando como contingência.

## Publicação no Render

1. Publique este repositório como **Web Service Python** (não como Static Site).
2. Use a raiz do repositório como diretório raiz e o `render.yaml` incluído.
3. Configure `DATABASE_URL` com a mesma conexão PostgreSQL usada pelos módulos
   compartilhados, `PORTAL_SESSION_SECRET` e `ERP_PORTAL_SSO_SECRET`.
4. Em Cadastro, Estoque, Suprimentos e MES, configure o mesmo
   `ERP_PORTAL_SSO_SECRET`, `ERP_PORTAL_URL=https://ji-portal-operacional.onrender.com`
   e `ERP_PORTAL_SSO_ENABLED=1` somente após o Portal estar saudável.

Nunca exponha essas variáveis no navegador ou no repositório. O Portal usa a
tabela `public.users` exclusivamente para validar o login; as permissões
continuam sendo impostas por cada módulo.
