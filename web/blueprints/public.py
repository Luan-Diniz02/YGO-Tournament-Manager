from flask import Blueprint, flash, jsonify, redirect, render_template, url_for
from web.services.public_service import PublicService


def create_public_blueprint(conexao, ordenar_duelistas_para_rank):
    public_bp = Blueprint('public', __name__)
    public_service = PublicService(conexao, ordenar_duelistas_para_rank)

    @public_bp.route('/')
    def index():
        return render_template('index.html')

    @public_bp.route('/health')
    def healthcheck():
        payload, status_code = public_service.health_status()
        return jsonify(payload), status_code

    @public_bp.route('/ranking')
    def ranking():
        try:
            duelistas_ordenados = public_service.carregar_ranking()
        except Exception:
            duelistas_ordenados = []
            flash('Nao foi possivel carregar o ranking agora. Verifique a conexao com o banco e tente novamente.', 'error')
        return render_template('ranking.html', duelistas=duelistas_ordenados)

    @public_bp.route('/dashboard')
    def dashboard_estatisticas():
        dados_dashboard = public_service.dashboard_default()

        try:
            dados_dashboard = public_service.carregar_dashboard()
        except Exception:
            flash('Nao foi possivel carregar o dashboard agora. Verifique a conexao com o banco e tente novamente.', 'error')

        return render_template('dashboard_estatisticas.html', dashboard=dados_dashboard)

    @public_bp.route('/dashboard/duelista/<path:nome>')
    def dashboard_duelista(nome):
        try:
            dados_duelista = public_service.carregar_dashboard_duelista(nome)
        except Exception:
            dados_duelista = None
            flash('Nao foi possivel carregar as estatisticas deste duelista agora.', 'error')

        if not dados_duelista:
            flash('Duelista nao encontrado para visualizacao de estatisticas.', 'error')
            return redirect(url_for('public.dashboard_estatisticas'))

        return render_template('dashboard_duelista.html', dados=dados_duelista)

    @public_bp.route('/visualizar_torneios')
    def visualizar_torneios():
        torneios_bd = public_service.listar_torneios()
        return render_template('visualizar_torneios.html', torneios=torneios_bd)

    @public_bp.route('/torneio/<int:id>')
    def painel_torneio(id):
        dados_painel = public_service.carregar_painel_torneio(id)
        if not dados_painel:
            flash('Torneio nao encontrado!', 'error')
            return redirect(url_for('public.visualizar_torneios'))

        return render_template(
            'painel_torneio.html',
            torneio=dados_painel['torneio'],
            participantes=dados_painel['participantes'],
            todos_duelistas=dados_painel['todos_duelistas'],
        )

    return public_bp
