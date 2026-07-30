# Portal Operacional — JI Montadora

Portal estático de acesso aos módulos operacionais. Não possui banco de dados,
autenticação própria nem credenciais: cada link abre o módulo correspondente,
que mantém seu login e suas permissões atuais.

## Publicação no Render

1. Crie um **Static Site** no Render a partir deste repositório.
2. Defina o diretório raiz como `portal-acesso-ji`.
3. Use `render.yaml` ou configure `Publish Directory` como `.`.
4. Não é necessário incluir variáveis de ambiente ou Supabase.

Os links dos módulos ficam diretamente em `index.html`.
