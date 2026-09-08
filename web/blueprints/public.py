from flask import Blueprint, flash, jsonify, redirect, render_template, url_for, request
from web.services.public_service import PublicService


def create_public_blueprint(conexao, ordenar_duelistas_para_rank):
    public_bp = Blueprint('public', __name__)
    public_service = PublicService(conexao, ordenar_duelistas_para_rank)

    @public_bp.route('/')
    def index():
        temp_ativa = public_service.obter_temporada_ativa()
        return render_template('index.html', temporada_ativa=temp_ativa)

    @public_bp.route('/health')
    def healthcheck():
        payload, status_code = public_service.health_status()
        return jsonify(payload), status_code

    @public_bp.route('/ranking')
    def ranking():
        return redirect(url_for('public.dashboard_estatisticas'))

    @public_bp.route('/dashboard')
    def dashboard_estatisticas():
        temporadas = public_service.listar_temporadas()
        temp_ativa = public_service.obter_temporada_ativa()
        
        # Padrão: temporada ativa
        temporada_id = request.args.get('temporada')
        if temporada_id is None:
            temporada_id = str(temp_ativa['id']) if temp_ativa else 'geral'

        # Converte para int quando for numérico (garante branch correto no banco)
        if temporada_id and temporada_id != 'geral':
            try:
                temporada_id = int(temporada_id)
            except (ValueError, TypeError):
                temporada_id = 'geral'

        data_inicio = request.args.get('data_inicio') or ''
        data_fim = request.args.get('data_fim') or ''

        dados_dashboard = public_service.dashboard_default()
        try:
            dados_dashboard = public_service.carregar_dashboard(
                temporada_id,
                data_inicio or None,
                data_fim or None
            )
        except Exception as e:
            flash(f'Nao foi possivel carregar o dashboard agora. Erro: {e}', 'error')

        # temporada_atual sempre como str para a comparação Jinja2 no dropdown
        return render_template(
            'dashboard_estatisticas.html', 
            dashboard=dados_dashboard,
            temporadas=temporadas,
            temporada_atual=str(temporada_id),
            data_inicio=data_inicio,
            data_fim=data_fim
        )

    @public_bp.route('/dashboard/duelista/<path:nome>')
    def dashboard_duelista(nome):
        temporadas = public_service.listar_temporadas()
        temp_ativa = public_service.obter_temporada_ativa()
        
        temporada_id = request.args.get('temporada')
        if temporada_id is None:
            temporada_id = str(temp_ativa['id']) if temp_ativa else 'geral'

        # Converte para int quando for numérico (garante branch correto no banco)
        if temporada_id and temporada_id != 'geral':
            try:
                temporada_id = int(temporada_id)
            except (ValueError, TypeError):
                temporada_id = 'geral'

        data_inicio = request.args.get('data_inicio') or ''
        data_fim = request.args.get('data_fim') or ''

        try:
            dados_duelista = public_service.carregar_dashboard_duelista(
                nome, temporada_id, data_inicio or None, data_fim or None
            )
        except Exception:
            dados_duelista = None
            flash('Nao foi possivel carregar as estatisticas deste duelista agora.', 'error')

        if not dados_duelista:
            flash('Duelista nao encontrado para visualizacao de estatisticas.', 'error')
            return redirect(url_for('public.dashboard_estatisticas'))

        # temporada_atual sempre como str para a comparação Jinja2 no dropdown
        return render_template(
            'dashboard_duelista.html', 
            dados=dados_duelista,
            temporadas=temporadas,
            temporada_atual=str(temporada_id),
            data_inicio=data_inicio,
            data_fim=data_fim
        )

    @public_bp.route('/visualizar_torneios')
    def visualizar_torneios():
        torneios_bd = public_service.listar_torneios()
        temporadas = public_service.listar_temporadas()
        return render_template('visualizar_torneios.html', torneios=torneios_bd, temporadas=temporadas)

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
