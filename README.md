# Liga YGO Marabá — Tournament Manager

Aplicação web em Flask para gerenciamento de torneios de Yu-Gi-Oh!, com ranking unificado,
perfis individuais de duelistas, painel por etapa, temporadas e área administrativa protegida.

## Demo

- Produção (Render): https://ygo-tournament-manager.onrender.com
- Healthcheck: https://ygo-tournament-manager.onrender.com/health

---

## Principais Recursos

- Cadastro e gerenciamento de etapas de torneio (com edição de nome, rodadas e data)
- **Temporadas**: agrupamento de torneios em períodos competitivos com nome e datas
- **Ranking unificado** com pontos, Win Rate, Top Cut, Títulos e conversão Top/Título
- **Filtro de ranking por temporada**: cada temporada exibe apenas as estatísticas dos torneios que a compõem
- **Perfil individual** por duelista: histórico por etapa, conquistas contextuais e métricas
- Controle de Top Cut e colocação final por participante
- Área administrativa com sessão, proteção CSRF e restrição por IP
- Layout responsivo (desktop/mobile) com sistema de cards adaptativo

---

## Arquitetura

```text
ygo-tournament-manager/
+-- core/
|   +-- database_conexao.py   # Acesso a dados (MySQL) e lógica de query
|   +-- models.py             # Dataclasses (Duelistas, etc.)
+-- web/
|   +-- app.py                # Entry point Flask
|   +-- routes.py             # Registro de blueprints
|   +-- auth.py               # Guard de autenticação admin
|   +-- security.py           # CSRF, secret key, redirect seguro
|   +-- blueprints/
|   |   +-- admin.py          # Rotas administrativas (protegidas)
|   |   +-- public.py         # Rotas públicas
|   +-- services/
|   |   +-- admin_service.py  # Regras de negócio admin
|   |   +-- public_service.py # Regras de negócio públicas
|   +-- templates/            # Jinja2 (ver docs/CONTEXT.md para mapa completo)
|   +-- static/
|       +-- css/style.css     # CSS global do projeto
|       +-- js/script.js      # JS global (validações, confirmações, etc.)
+-- docs/
|   +-- CONTEXT.md            # Regras de UI/UX, arquitetura e decisões do projeto
+-- scripts/
|   +-- run.bat               # Inicialização Windows (CMD)
|   +-- run.ps1               # Inicialização Windows (PowerShell)
+-- tests/                    # Testes unitários e de integração HTTP
+-- schema.sql                # DDL para criação manual das tabelas
+-- requirements.txt
+-- requirements-dev.txt
+-- render.yaml               # Deploy no Render (Blueprint)
+-- Procfile
```

> Consulte [`docs/CONTEXT.md`](docs/CONTEXT.md) para o mapa completo de rotas,
> padrões visuais e regras de negócio consolidadas.

---

## Requisitos

- Python 3.10+
- MySQL (ou TiDB compatível com MySQL)

## Instalação

```bash
pip install -r requirements.txt
```

Para desenvolvimento e testes:

```bash
pip install -r requirements-dev.txt
```

## Configuração de Ambiente

Copie `.env.example` para `.env` e preencha as variáveis:

| Variável | Descrição |
|---|---|
| `FLASK_SECRET_KEY` | **Obrigatória.** Chave da sessão Flask |
| `AUTO_INIT_DB` | `1` para criar tabelas automaticamente no boot |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Conexão MySQL |
| `DB_SSL_DISABLED`, `DB_SSL_CA`, `DB_SSL_VERIFY_CERT`, `DB_SSL_VERIFY_IDENTITY` | TLS/SSL |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Credenciais do painel admin |
| `ADMIN_ALLOWED_IPS` | IPs permitidos para o admin (opcional) |

## Como Executar

### Windows (recomendado)

```bat
scripts\run.bat
```

ou

```powershell
.\scripts\run.ps1
```

### Geral

```bash
python -m web.app
```

A aplicação sobe em `http://localhost:5000`.

---

## Testes

```bash
# Executar suíte completa
pytest -q

# Com cobertura
pytest --cov=web --cov-report=term-missing -q
```

Cobertura inclui:
- Testes unitários de services (`tests/test_admin_service.py`, `test_public_service.py`)
- Testes de integração HTTP (`tests/test_http_integration.py`)
- Testes de segurança (`tests/test_security.py`)

---

## Deploy (Render + TiDB)

1. Crie banco MySQL/TiDB e obtenha credenciais
2. Suba o serviço via `render.yaml` (Blueprint do Render)
3. Configure variáveis de ambiente (`DB_*`, `FLASK_SECRET_KEY`, etc.)
4. No primeiro deploy, use `AUTO_INIT_DB=1`
5. Valide `GET /health` e os fluxos principais

Comandos de deploy esperados:
- **Build:** `pip install -r requirements.txt`
- **Start:** `gunicorn web.app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

---

## Troubleshooting

**`ModuleNotFoundError` ao iniciar**
- Use `python -m web.app` (não `python web/app.py`)

**Erro de conexão com banco**
- Verifique variáveis `DB_*` e configurações SSL do provedor

**Porta 5000 em uso**
```powershell
$env:PORT=8080; python -m web.app
```

---

## Licença

MIT
