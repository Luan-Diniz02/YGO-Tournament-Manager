import os
from dotenv import load_dotenv
from flask import Flask
from core.database_conexao import Conexao
from web.auth import inject_auth_context
from web.routes import register_routes
from web.security import configure_security

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
configure_security(app)

# Instancia da conexão
conexao = Conexao()
app.context_processor(inject_auth_context)


def inicializar_estrutura_banco_se_necessario():
    auto_init_db = os.getenv('AUTO_INIT_DB', '0') == '1'
    if not auto_init_db:
        return

    conexao.garantir_estrutura_bd()


inicializar_estrutura_banco_se_necessario()


def ordenar_duelistas_para_rank(duelistas):
    # Ranking: mais pontos primeiro; em empate, menos derrotas.
    return sorted(duelistas, key=lambda d: (-d.pontos, d.derrotas, d.nome.casefold()))


register_routes(app, conexao, ordenar_duelistas_para_rank)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)