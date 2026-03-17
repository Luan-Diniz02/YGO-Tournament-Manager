# Liga YGO Marabá - Interface Web Flask

Este projeto foi migrado de uma interface desktop Tkinter para uma aplicação web usando Flask.

## Estrutura do Projeto

```
GT_BD_Interface/
├── app.py                 # Aplicação Flask principal
├── Conexao.py            # Classe para conexão com banco de dados
├── Duelistas_Torneio.py  # Classes Duelistas e Torneio
├── Interface.py          # Interface Tkinter original (mantida para referência)
├── Main.py               # Arquivo principal da versão Tkinter
├── requirements.txt      # Dependências do projeto
├── static/
│   ├── css/
│   │   └── style.css    # Estilos customizados
│   └── js/
│       └── script.js    # JavaScript para interatividade
└── templates/
    ├── base.html         # Template base
    ├── index.html        # Página inicial
    ├── cadastrar_torneio.html
    ├── cadastrar_pontos.html
    ├── buscar_duelista.html
    ├── alterar_duelista.html
    ├── ranking.html
    └── visualizar_torneios.html
```

## Instalação

1. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar banco de dados:**
   - Certifique-se de que o MySQL está executando
   - As configurações de conexão estão em `Conexao.py`:
     - Host: 127.0.0.1
     - User: root
     - Password: root
     - Database: torneio

## Executando a Aplicação

### Método 1: Executar diretamente
```bash
python app.py
```

### Método 2: Usando Flask CLI
```bash
set FLASK_APP=app.py
set FLASK_ENV=development
flask run
```

### Método 3: PowerShell (Windows)
```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
flask run
```

A aplicação estará disponível em: http://localhost:5000

## Funcionalidades

### ✅ Implementadas
- **Página Inicial**: Menu principal com navegação intuitiva
- **Cadastrar Torneio**: Formulário para cadastrar novos torneios
- **Cadastrar Pontos**: Adicionar pontos para duelistas (novos ou existentes)
- **Buscar Duelista**: Pesquisar duelistas específicos com filtro
- **Ranking**: Visualizar ranking completo ordenado por pontos
- **Alterar Duelista**: Editar dados de duelistas existentes
- **Atualizar BD**: Sincronizar dados com o banco

### 🚧 Em Desenvolvimento
- **Visualizar Torneios**: Lista e detalhes dos torneios cadastrados

## Sistema de Pontuação

- **Vitória**: 3 pontos
- **Empate**: 1 ponto
- **Derrota**: 0 pontos
- **Participação**: 1 ponto adicional por torneio

## Recursos da Interface Web

### Design
- Interface responsiva usando Bootstrap 5
- Tema customizado com cores da Liga YGO
- Animações e efeitos visuais modernos
- Icons Font Awesome para melhor usabilidade

### Funcionalidades JavaScript
- Validação de formulários em tempo real
- Notificações toast automáticas
- Animações de carregamento
- Atalhos de teclado (Ctrl+Enter para submeter, Esc para voltar)
- Confirmações para ações destrutivas
- Funcionalidade de impressão do ranking

### Melhorias de UX
- Mensagens de feedback claras
- Auto-ocultação de alertas
- Navegação intuitiva
- Responsividade para dispositivos móveis
- Validação visual de campos

## Estrutura do Banco de Dados

### Tabela: duelistas
- id (int, auto_increment, primary key)
- nome (varchar)
- vitorias (int)
- derrotas (int)
- empates (int)
- participacao (int)
- pontos (int)

### Tabela: torneios (requer criação)
- id (int, auto_increment, primary key)
- nome (varchar)
- rodadas (int)
- quant_duelistas (int)
- data (date)

## Migração da Interface Tkinter

A migração manteve toda a funcionalidade original:

### Equivalências
| Tkinter | Flask Web |
|---------|-----------|
| `menu_torneio()` | `/cadastrar_torneio` |
| `menu_duelista()` | `/cadastrar_pontos` |
| `menu_buscar_duelista()` | `/buscar_duelista` |
| `menu_visualizar()` | `/ranking` |
| `menu_alterar_duelista()` | `/alterar_duelista/<nome>` |

### Vantagens da Versão Web
- Acesso remoto via navegador
- Interface mais moderna e responsiva
- Melhor experiência do usuário
- Facilidade de manutenção
- Possibilidade de múltiplos usuários simultâneos
- Integração mais fácil com outros sistemas

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