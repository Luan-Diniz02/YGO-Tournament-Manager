# Liga YGO Marabá - Interface Web Flask

Este projeto é uma aplicação web feita em Python (Flask) para o gerenciamento de torneios de Yu-Gi-Oh!, incluindo o cadastro de duelistas, pontos, ranking e configuração de torneios.

## Estrutura do Projeto

```
ygo-tournament-manager/
├── ACESSO_MOBILE.md      # Instruções para acessar via celular na mesma rede
├── README.md             # Documentação principal
├── requirements.txt      # Dependências do projeto (Flask, MySQL, etc)
├── core/                 # Lógica de negócio e banco de dados
│   ├── database_conexao.py # Classe e configuração da conexão com MySQL
│   └── models.py         # Modelos de dados do sistema (Duelistas, Torneios)
├── scripts/              # Scripts utilitários de execução e configuração
│   ├── liberar_firewall.bat
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
   - Verifique ou altere as credenciais de banco de dados em `core/database_conexao.py` conforme o ambiente:
     - Host: `127.0.0.1` (ou `localhost`)
     - User: `root`
     - Password: `root` (ou a senha configurada no seu MySQL)
     - Database: `torneio`

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

Se quiser acessar pelo celular (em rede local), consulte o arquivo `ACESSO_MOBILE.md` e, caso necessário, utilize o script `scripts\liberar_firewall.bat`.

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