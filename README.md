# Liga YGO Marabá — Tournament Manager

Aplicação web em Flask desenvolvida para o gerenciamento completo e moderno de torneios competitivos de Yu-Gi-Oh!, incluindo ranking unificado com pódio, métricas avançadas de desempenho, perfis individuais de duelistas, histórico detalhado de torneios, sistema de temporadas e painel administrativo protegido.

## Demo

- **Produção (Render):** https://ygo-tournament-manager.onrender.com
- **Healthcheck:** https://ygo-tournament-manager.onrender.com/health

---

## Principais Recursos

### 🏆 Experiência Competitiva & Métricas
- **Ranking Unificado:** Classificação atualizada por pontos, Vitórias/Derrotas, Win Rate, participações em Top Cut e número de títulos.
- **Pódio Visual Interativo:** Destaque para o Top 3 com avatares estilizados, pilares comemorativos e insígnias metálicas (🥇 1º Ouro, 🥈 2º Prata e 🥉 3º Bronze).
- **Indicadores Visuais de Desempenho:** Mini barras horizontais de progresso integradas para **Win Rate** e **Taxa de Conversão Top Cut → Título** (com exibição limpa em travessão `—` para duelistas sem participações em Top Cut).
- **Regras Oficiais Konami (Double Loss):** Alinhado à Tournament Policy moderna de Yu-Gi-Oh!, sem empates — partidas não resolvidas resultam em Double Loss (0 pontos e contabilizado em Derrotas).
- **Perfil Individual do Duelista:**
  - Histórico completo torneio a torneio (placar, rodadas, colocação no torneio e indicador de Top Cut, com colocação à esquerda do Top Cut).
  - Gráfico em rosca de distribuição de partidas (Vitórias vs Derrotas) com porcentagens dinâmicas na legenda e nos tooltips, mantendo o centro limpo para evitar redundâncias com o KPI card superior.
  - Gráfico de linha interativo da evolução cronológica de pontos por torneio com intervalos de 3 pontos no eixo Y, datas formatadas no eixo X (`dd/mm/aa`), tooltip detalhado e filtro de amostragem ("Últimos 4" torneios ou "Todos").
  - Conquistas automáticas contextuais (*Líder do Ranking*, *Rei do Top Cut*, *Maior Campeão*, *Elite Win Rate*).
- **Card Oficial do Duelista (Duelist Identity Card):** Cartão de identidade compartilhável com dados da temporada, métricas principais e insígnias, com exportação em imagem PNG em alta resolução (`html2canvas`) e compartilhamento genérico nativo via Web Share API com anexo direto da imagem e fallback inteligente.
- **Card de Compartilhamento do Ranking da Liga:** Modal exclusivo para exportação da classificação completa da temporada ou All-Time em imagem PNG de alta resolução (`html2canvas`) e compartilhamento nativo via Web Share API anexando a imagem gerada e link direto.

### 📅 Temporadas & Torneios
- **Gerenciamento de Temporadas:** Agrupamento de torneios em períodos competitivos com data de início e fim.
- **Filtro de Ranking por Temporada:** Subqueries otimizadas que omitem duelistas sem participações no período selecionado, exibindo apenas dados válidos para a temporada ativa ou All-Time.
- **Vínculo Híbrido:** Torneios vinculados à temporada ativa por padrão, com flexibilidade para ajustes retroativos no painel administrativo.
- **Exclusão Segura:** Desvinculação com chave estrangeira `ON DELETE SET NULL`, preservando o histórico geral dos torneios.

### 🎨 Design System & Mobile First
- **Suporte Nativo a Temas (Dark Mode & Light Mode):** Alternância instantânea com detecção automática da preferência do sistema operacional (`prefers-color-scheme`), contraste elevado no modo claro e persistência em `localStorage`.
- **Navegação Otimizada para Mobile:** Barra de navegação inferior (*bottom navigation bar*) com acesso rápido a Início, Ranking, Torneios, Menu Admin e Alternador de Tema.
- **Grids e Centralização Simétrica Mobile:** Visualização mobile de torneios, perfil de duelista (placar, rodadas, posição) e busca de duelistas em grades balanceadas com estatísticas perfeitamente centralizadas.
- **Admin Action Sheet (Offcanvas):** Menu flutuante moderno para administradores em smartphones, centralizando cadastros e gestão do sistema.
- **Modais Harmonizados:** Janelas de criação, edição e compartilhamento com suporte a rolagem interna (`modal-dialog-scrollable`) e botões de ação fixos no rodapé, totalmente adaptadas aos temas claro e escuro, sem quebra de contraste ou estilos padrão de navegador.

### 🔒 Segurança & Administração
- Autenticação administrativa com sessão protegida e timeout.
- Proteção contra ataques CSRF em todos os formulários e rotas com mutação de estado.
- Restrição opcional de acesso por IP (`ADMIN_ALLOWED_IPS`).
- Inicialização segura de banco de dados com migração de tabelas sob demanda.

---

## Arquitetura

```text
ygo-tournament-manager/
├── core/
│   ├── database_conexao.py   # Camada de persistência (MySQL) e queries agregadas
│   └── models.py             # Modelos de dados e dataclasses
├── web/
│   ├── app.py                # Ponto de entrada e configuração do Flask
│   ├── routes.py             # Registro e inicialização de blueprints
│   ├── auth.py               # Middleware e guards de autenticação admin
│   ├── security.py           # Gestão de CSRF, secret keys e sanitização de redirects
│   ├── blueprints/
│   │   ├── admin.py          # Rotas administrativas (painel protegido)
│   │   └── public.py         # Rotas públicas (landing, ranking, perfis, torneios)
│   ├── services/
│   │   ├── admin_service.py  # Regras de negócio da administração
│   │   └── public_service.py # Regras de negócio da consulta pública
│   ├── templates/            # Templates Jinja2 organizados por responsabilidade
│   └── static/
│       ├── css/style.css     # Design System global (tokens CSS, dark/light themes)
│       └── js/script.js      # Scripts cliente (validações, modais, tema)
├── docs/
│   └── CONTEXT.md            # Documentação de decisões arquiteturais e regras visuais
├── scripts/
│   ├── run.bat               # Script de execução rápida Windows (CMD)
│   └── run.ps1               # Script de execução rápida Windows (PowerShell)
├── tests/                    # Suíte de testes unitários e de integração HTTP
├── schema.sql                # DDL do esquema de banco de dados
├── requirements.txt          # Dependências de produção
├── requirements-dev.txt      # Dependências de desenvolvimento e testes
├── render.yaml               # Configuração de deploy no Render (Blueprint)
└── Procfile                  # Processo web para servidores WSGI
```

> Para detalhes das decisões técnicas, regras de cálculo e convenções de rotas, consulte [`docs/CONTEXT.md`](docs/CONTEXT.md).

---

## Requisitos

- Python 3.10+
- MySQL 8.0+ ou TiDB (compatível com MySQL)

## Instalação

Clone o repositório e configure seu ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate  # No Linux/macOS
# ou no Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```

Para instalar as dependências de desenvolvimento e testes:

```bash
pip install -r requirements-dev.txt
```

## Configuração de Ambiente

Crie o arquivo `.env` com base no `.env.example`:

```bash
cp .env.example .env
```

Parâmetros de configuração:

| Variável | Descrição |
|---|---|
| `FLASK_SECRET_KEY` | **Obrigatória.** Chave para assinatura da sessão Flask. |
| `AUTO_INIT_DB` | `1` para criar/atualizar a estrutura de tabelas automaticamente no boot. |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Credenciais da conexão MySQL/TiDB. |
| `DB_SSL_DISABLED`, `DB_SSL_CA`, `DB_SSL_VERIFY_CERT`, `DB_SSL_VERIFY_IDENTITY` | Opções de criptografia TLS/SSL da base de dados. |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Credenciais para acesso à área administrativa. |
| `ADMIN_ALLOWED_IPS` | Lista de IPs permitidos para a área admin (opcional, separados por vírgula). |

## Como Executar

### Windows

```bat
scripts\run.bat
```
ou via PowerShell:
```powershell
.\scripts\run.ps1
```

### Geral (Linux / macOS / Manual)

```bash
python -m web.app
```

A aplicação estará disponível em `http://localhost:5000`.

---

## Testes Automatizados

A suíte de testes cobre regras de negócio, serviços, integridade HTTP e segurança:

```bash
# Executar suíte completa de testes
pytest -q

# Executar com relatório de cobertura
pytest --cov=web --cov-report=term-missing -q
```

---

## Deploy (Render + TiDB)

A aplicação está configurada para deploy contínuo no Render utilizando o `render.yaml`:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn web.app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

No primeiro deploy em uma nova base de dados, garanta `AUTO_INIT_DB=1` nas variáveis de ambiente do serviço para criação automática das tabelas.

---

## Licença

Este projeto está licenciado sob os termos da licença [MIT](LICENSE).
