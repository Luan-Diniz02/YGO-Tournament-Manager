# Liga YGO Marabá - Tournament Manager

Aplicação web em Flask para gerenciamento de torneios de Yu-Gi-Oh, com ranking, dashboards, painel de torneio e área administrativa protegida.

## Demo

- Produção (Render): https://ygo-tournament-manager.onrender.com
- Healthcheck: https://ygo-tournament-manager.onrender.com/health

## Principais Recursos

- Cadastro e gerenciamento de torneios
- Ranking global de duelistas
- Dashboard geral e dashboard individual por duelista
- Controle de Top Cut por participante
- Área administrativa com sessão
- Proteção CSRF em formulários mutáveis
- Redirecionamento seguro no login admin

## Arquitetura

- `core/`: acesso a dados e modelos
- `web/blueprints/`: camada HTTP (rotas públicas e admin)
- `web/services/`: regras de negócio
- `web/security.py`: CSRF, redirect seguro, secret key obrigatória
- `web/auth.py`: autenticação/admin guard

Estrutura resumida:

```text
ygo-tournament-manager/
|- core/
|  |- database_conexao.py
|  `- models.py
|- web/
|  |- app.py
|  |- routes.py
|  |- auth.py
|  |- security.py
|  |- blueprints/
|  |  |- admin.py
|  |  `- public.py
|  |- services/
|  |  |- admin_service.py
|  |  `- public_service.py
|  |- templates/
|  `- static/
|- scripts/
|  |- run.bat
|  `- run.ps1
|- requirements.txt
|- requirements-dev.txt
|- render.yaml
|- Procfile
`- schema.sql
```

## Requisitos

- Python 3.10+
- MySQL (ou TiDB compatível MySQL)

## Instalação

```bash
pip install -r requirements.txt
```

Para desenvolvimento e testes:

```bash
pip install -r requirements-dev.txt
```

## Configuração de Ambiente

Variáveis principais:

- `FLASK_SECRET_KEY` (obrigatória)
- `AUTO_INIT_DB` (`0` ou `1`)
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `DB_SSL_DISABLED`, `DB_SSL_CA`, `DB_SSL_VERIFY_CERT`, `DB_SSL_VERIFY_IDENTITY`
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`
- `ADMIN_ALLOWED_IPS` (opcional)

Use `.env.example` como referência.

## Como Executar

### Opção 1 (recomendada no Windows)

```bash
scripts\run.bat
```

ou

```powershell
.\scripts\run.ps1
```

### Opção 2 (recomendada em geral)

```bash
python -m web.app
```

A aplicação sobe em `http://localhost:5000`.

## Testes

Executar suíte:

```bash
pytest -q
```

Executar com cobertura:

```bash
pytest --cov=web --cov-report=term-missing -q
```

Cobertura atual inclui:

- Testes unitários de services
- Testes de integração HTTP (login admin, CSRF, redirect seguro e rotas admin)

## Deploy (Render + TiDB)

1. Crie banco MySQL/TiDB e obtenha credenciais
2. Suba o serviço no Render via `render.yaml` (Blueprint)
3. Configure variáveis de ambiente (`DB_*`, `FLASK_SECRET_KEY`, etc.)
4. No primeiro deploy, opcionalmente use `AUTO_INIT_DB=1`
5. Valide `GET /health` e fluxos principais

Comandos de deploy esperados:

- Build: `pip install -r requirements.txt`
- Start: `gunicorn web.app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

## Troubleshooting

### ModuleNotFoundError ao iniciar

Use:

```bash
python -m web.app
```

### Erro de conexão com banco

- Verifique se o banco está ativo
- Revise `DB_*`
- Confirme SSL/TLS conforme o provedor

### Porta 5000 em uso

```powershell
$env:PORT=8080
python -m web.app
```

## Licença

MIT
