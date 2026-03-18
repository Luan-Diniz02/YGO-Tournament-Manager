# Liga YGO Marabá - Interface Web Flask

Este projeto é uma aplicação web feita em Python (Flask) para o gerenciamento de torneios de Yu-Gi-Oh!, incluindo o cadastro de duelistas, pontos, ranking e configuração de torneios.

## Demo

- Produção (Render): https://ygo-tournament-manager.onrender.com
- Healthcheck: https://web-production-af74b.up.railway.app/health

## Destaques de Portfólio

- Deploy em produção com variáveis de ambiente e healthcheck
- Modo público e modo administrador com autenticação por sessão
- Controle de edição por permissões e placar público por torneio
- Organização em camadas (`core/` e `web/`)
- CI com validação automática de sintaxe Python
- Licença MIT para uso e distribuição

## Estrutura do Projeto

```
ygo-tournament-manager/
├── .github/             # CI com GitHub Actions
├── .env.example         # Exemplo de variáveis de ambiente
├── LICENSE              # Licença MIT
├── README.md             # Documentação principal
├── requirements.txt      # Dependências do projeto (Flask, MySQL, etc)
├── render.yaml           # Blueprint de deploy no Render
├── Procfile              # Comando de start para plataformas PaaS
├── schema.sql            # Estrutura do banco
├── core/                 # Lógica de negócio e banco de dados
│   ├── database_conexao.py # Classe e configuração da conexão com MySQL
│   └── models.py         # Modelos de dados do sistema (Duelistas, Torneios)
├── scripts/              # Scripts utilitários de execução e configuração
│   ├── run.bat           # Script de atalho para rodar a aplicação em Windows
│   └── run.ps1           # Script PowerShell para iniciar a aplicação
└── web/                  # Aplicação web e rotas Flask
    ├── app.py            # Inicialização e rotas do Flask
    ├── static/           # Arquivos estáticos (CSS, JS)
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── script.js
    └── templates/        # Arquivos HTML (Páginas Web)
        ├── alterar_duelista.html
        ├── base.html
        ├── buscar_duelista.html
        ├── cadastrar_torneio.html
        ├── index.html
        ├── painel_torneio.html
        ├── ranking.html
        └── visualizar_torneios.html
```

## Instalação

1. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar banco de dados:**
   - Certifique-se de que o servidor MySQL está em execução.
    - Configure as variáveis de ambiente do banco conforme seu ambiente.
    - Exemplo local (desenvolvimento):
       - Host: `127.0.0.1`
       - Port: `3306`
       - User: `seu_usuario_local`
       - Password: `sua_senha_local`
       - Database: `torneio`
    - Em produção, use sempre as variáveis `DB_*` do provedor e credenciais fortes.

## Executando a Aplicação

### Método 1: Usando os Scripts Prontos (Windows)
A forma mais ágil de dar start no projeto é utilizando os arquivos em `scripts/`.
```bash
# Executando via Batch (CMD)
scripts\run.bat

# Ou via PowerShell
.\scripts\run.ps1
```

### Método 2: Executar via Python diretamente
Certifique-se de que seu terminal esteja na pasta raiz do projeto e execute:
```bash
python -m web.app
```

A aplicação estará disponível em: `http://localhost:5000`

Em produção, utilize a URL pública da seção Demo.

## Deploy em Produção (Render + TiDB)

### 1. Pré-requisitos
- Conta no Render
- Conta no TiDB Cloud Serverless (MySQL compatível)

### 2. Deploy rápido (Render Free + TiDB)

Passo a passo (15-20 minutos):
1. Crie um cluster no TiDB Cloud Serverless.
2. Copie as credenciais de conexão: host, porta, usuário, senha e nome do database.
3. No Render, crie o serviço via Blueprint usando `render.yaml`.
4. Configure as variáveis de ambiente `DB_*` no serviço web.
5. No primeiro deploy, mantenha `AUTO_INIT_DB=1` para criar as tabelas automaticamente.
6. Após validar o sistema em produção, altere para `AUTO_INIT_DB=0` e faça novo deploy.
7. Teste `GET /health` e os fluxos principais (ranking, torneios e permissões admin).

Observações do plano free da Render:
- Pode ocorrer cold start após inatividade.
- Recursos de CPU/RAM são limitados.
- Ideal para MVP, homologação e tráfego baixo.

### 3. Arquivos de produção já incluídos no projeto
- `Procfile`
- `render.yaml`
- `schema.sql`
- `.env.example`

### 4. Deploy automatizado com Blueprint (render.yaml)
1. No Render, clique em **New +** > **Blueprint**.
2. Selecione o repositório.
3. O Render detectará automaticamente o arquivo `render.yaml`.
4. Revise o plano e confirme a criação do serviço.

Com isso, `buildCommand`, `startCommand`, `healthCheckPath` e `autoDeploy` já serão aplicados automaticamente.

### 5. Criar banco e tabelas
Você tem duas opções:
- Executar `schema.sql` manualmente no MySQL de produção.
- Usar `AUTO_INIT_DB=1` no Render para a aplicação criar as tabelas automaticamente no startup.

### 6. Variáveis de ambiente no Render
Configure no serviço web:
- `FLASK_SECRET_KEY`
- `AUTO_INIT_DB`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DB_SSL_DISABLED` (opcional, default `0`)
- `DB_SSL_CA` (opcional, caminho de certificado CA)
- `DB_SSL_VERIFY_CERT` (opcional, `0`/`1`)
- `DB_SSL_VERIFY_IDENTITY` (opcional, `0`/`1`)

Exemplo para ambiente local sem TLS:
- `DB_SSL_DISABLED=1`

Exemplo comum para banco gerenciado com TLS:
- `DB_SSL_DISABLED=0`
- `DB_SSL_VERIFY_CERT=0`
- `DB_SSL_VERIFY_IDENTITY=0`

### 7. Build e start
O Render usará:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn web.app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

### 8. Pós-deploy
- Acesse a URL pública gerada pelo Render
- Teste os fluxos: busca, ranking, torneios, desativar/reativar duelista

### Observação importante
Mesmo com `render.yaml`, ainda é necessário informar as credenciais do MySQL (`DB_*`) caso seu banco esteja fora do Render.

## Funcionalidades

### ✅ Implementadas
- **Página Inicial**: Menu principal com navegação fácil e intuitiva.
- **Painel de Torneio e Cadastro**: Cadastro, edição e acompanhamento de torneios ativos.
- **Cadastro Geral e Pontos**: Registrar duelistas ou computar pontuação de um evento.
- **Busca Rápida de Duelistas**: Localizar e visualizar informações completas de um duelista.
- **Ranking**: Visualizar a listagem de todos os jogadores ordenada pelos pontos obtidos.
- **Alteração de Duelista**: Atualização ou correção dos dados existentes.

## Sistema de Pontuação Padrão
*(Conforme a regra do torneio ou liga)*
- **Vitória**: 3 pontos
- **Empate**: 1 ponto
- **Derrota**: 0 pontos
- **Participação**: 1 ponto adicional por torneio jogado

## Recursos da Interface
- **Design Web Responsivo**: Criado com Bootstrap, adaptável para telas grandes ou mobile.
- **Feedback Visual Avançado**: Uso de estilos CSS (animações) e `script.js` para validações rápidas.
- **Organização Arquitetural**: Separação clara de responsabilidades com a pasta `core/` (Dados/Modelos) e `web/` (Rotas/Telas).

## Controle de Acesso (Admin e Público)

- Usuário público: pode visualizar `Ranking`, `Visualizar Torneios` e o placar de cada torneio.
- Admin: possui acesso completo às rotas de gestão (cadastro, edição e exclusão).

### Variáveis de ambiente para admin
- `ADMIN_USERNAME` (exemplo: `admin`)
- `ADMIN_PASSWORD` (defina uma senha forte)
- `ADMIN_ALLOWED_IPS` (opcional, lista separada por vírgula para permitir login/admin apenas de IPs específicos)

### Rotas de autenticação
- Login admin: `/admin/login`
- Logout admin: `/admin/logout`

## Banco de Dados

### Tabela: `duelistas`
- `id` (int, auto_increment, primary key)
- `nome` (varchar)
- `vitorias` (int)
- `derrotas` (int)
- `empates` (int)
- `participacao` (int)
- `pontos` (int)

### Tabela: `torneios`
- `id` (int, auto_increment, primary key)
- `nome` (varchar)
- `rodadas` (int)
- `quant_duelistas` (int)
- `data` (date)

## Desenvolvimento

Para contribuir com o projeto:

1. Clone o repositório
2. Instale as dependências
3. Configure o banco de dados
4. Execute a aplicação em modo desenvolvimento
5. Faça suas alterações
6. Teste todas as funcionalidades

## Troubleshooting

### Erro de Conexão com Banco
- Verifique se o MySQL está executando
- Confirme as credenciais em `Conexao.py`
- Certifique-se de que o banco 'torneio' existe

### Erro de Módulo não Encontrado
```bash
pip install -r requirements.txt
```

### Porta 5000 em Uso
Altere a porta no final do arquivo `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

## Próximas Funcionalidades

- Implementar visualização completa de torneios
- Sistema de relatórios em PDF
- API REST para integração externa
- Sistema de backup automático
- Dashboard com estatísticas avançadas
- Sistema de notificações

## Contato

Para dúvidas ou sugestões sobre o sistema Liga YGO Marabá, entre em contato com a administração do torneio.