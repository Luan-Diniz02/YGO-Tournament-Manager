from web.blueprints.admin import create_admin_blueprint
from web.blueprints.public import create_public_blueprint


def register_routes(app, conexao, ordenar_duelistas_para_rank):
    app.register_blueprint(create_public_blueprint(conexao, ordenar_duelistas_para_rank))
    app.register_blueprint(create_admin_blueprint(conexao, ordenar_duelistas_para_rank))
