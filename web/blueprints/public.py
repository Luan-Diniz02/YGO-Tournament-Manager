from flask import Blueprint, flash, jsonify, redirect, render_template, url_for


def create_public_blueprint(conexao, ordenar_duelistas_para_rank):
    public_bp = Blueprint('public', __name__)

    @public_bp.route('/')
    def index():
        return render_template('index.html')

    @public_bp.route('/health')
    def healthcheck():
        conexao_bd = None
        cursor = None
        try:
            conexao_bd = conexao.conectar_bd()
            cursor = conexao_bd.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            return jsonify({'status': 'ok', 'database': 'up'}), 200
        except Exception as e:
            return jsonify({'status': 'degraded', 'database': 'down', 'error': str(e)}), 503
        finally:
            if cursor:
                cursor.close()
            if conexao_bd:
                conexao_bd.close()

    @public_bp.route('/ranking')
    def ranking():
        try:
            duelistas = conexao.carregar_duelistas()
            duelistas_ordenados = ordenar_duelistas_para_rank(duelistas)
        except Exception:
            duelistas_ordenados = []
            flash('Nao foi possivel carregar o ranking agora. Verifique a conexao com o banco e tente novamente.', 'error')
        return render_template('ranking.html', duelistas=duelistas_ordenados)

    @public_bp.route('/dashboard')
    def dashboard_estatisticas():
        dados_dashboard = {
            'resumo': {
                'total_duelistas': 0,
                'total_partidas': 0,
                'total_vitorias': 0,
                'total_derrotas': 0,
                'total_empates': 0,
                'total_tops': 0,
                'total_campeonatos': 0,
                'win_rate_geral': 0.0,
                'taxa_conversao_top_titulo_geral': 0.0,
            },
            'lideres': {
                'maior_win_rate': None,
                'mais_tops': None,
                'mais_campeonatos': None,
            },
            'duelistas': [],
        }

        try:
            dados_dashboard = conexao.obter_estatisticas_dashboard()
        except Exception:
            flash('Nao foi possivel carregar o dashboard agora. Verifique a conexao com o banco e tente novamente.', 'error')

        return render_template('dashboard_estatisticas.html', dashboard=dados_dashboard)

    @public_bp.route('/dashboard/duelista/<path:nome>')
    def dashboard_duelista(nome):
        try:
            dados_duelista = conexao.obter_estatisticas_duelista(nome)
        except Exception:
            dados_duelista = None
            flash('Nao foi possivel carregar as estatisticas deste duelista agora.', 'error')

        if not dados_duelista:
            flash('Duelista nao encontrado para visualizacao de estatisticas.', 'error')
            return redirect(url_for('public.dashboard_estatisticas'))

        return render_template('dashboard_duelista.html', dados=dados_duelista)

    @public_bp.route('/visualizar_torneios')
    def visualizar_torneios():
        torneios_bd = conexao.listar_torneios()
        return render_template('visualizar_torneios.html', torneios=torneios_bd)

    @public_bp.route('/torneio/<int:id>')
    def painel_torneio(id):
        torneio = conexao.get_torneio(id)
        if not torneio:
            flash('Torneio nao encontrado!', 'error')
            return redirect(url_for('public.visualizar_torneios'))

        participantes = conexao.listar_participantes_torneio(id)
        todos_duelistas = conexao.carregar_duelistas()
        return render_template(
            'painel_torneio.html',
            torneio=torneio,
            participantes=participantes,
            todos_duelistas=todos_duelistas,
        )

    return public_bp
