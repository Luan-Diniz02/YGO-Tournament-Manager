import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import os
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from core.models import Duelistas, Torneio
from core.database_conexao import Conexao

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
# Carrega a chave secreta a partir das variáveis de ambiente (com fallback seguro apenas para evitar quebrar bruscamente)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_if_env_not_found')

# Instancia da conexão
conexao = Conexao()


def admin_esta_logado():
    return session.get('is_admin', False)


def obter_ip_cliente():
    forwarded_for = request.headers.get('X-Forwarded-For', '').strip()
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return (request.remote_addr or '').strip()


def ip_admin_permitido():
    ips_permitidos = os.getenv('ADMIN_ALLOWED_IPS', '').strip()
    if not ips_permitidos:
        return True

    cliente_ip = obter_ip_cliente()
    allowlist = {ip.strip() for ip in ips_permitidos.split(',') if ip.strip()}
    return cliente_ip in allowlist


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not ip_admin_permitido():
            flash('Acesso administrativo bloqueado para este IP.', 'error')
            return redirect(url_for('index'))

        if admin_esta_logado():
            return func(*args, **kwargs)

        flash('Acesso restrito ao administrador. Faça login para continuar.', 'error')
        return redirect(url_for('admin_login', next=request.path))

    return wrapper


@app.context_processor
def inject_auth_context():
    return {
        'is_admin': admin_esta_logado(),
    }


def inicializar_estrutura_banco_se_necessario():
    auto_init_db = os.getenv('AUTO_INIT_DB', '0') == '1'
    if not auto_init_db:
        return

    conexao.garantir_estrutura_bd()


inicializar_estrutura_banco_se_necessario()


def ordenar_duelistas_para_rank(duelistas):
    # Ranking: mais pontos primeiro; em empate, menos derrotas.
    return sorted(duelistas, key=lambda d: (-d.pontos, d.derrotas, d.nome.casefold()))

@app.route('/')
def index():
    """Página inicial com menu principal"""
    return render_template('index.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if not ip_admin_permitido():
        flash('Login administrativo bloqueado para este IP.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', '')

        if not admin_password:
            flash('ADMIN_PASSWORD não está configurada no ambiente de produção.', 'error')
            return render_template('admin_login.html')

        if username == admin_username and password == admin_password:
            session['is_admin'] = True
            session['admin_username'] = admin_username
            flash('Login de administrador realizado com sucesso.', 'success')

            next_url = request.args.get('next') or request.form.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('index'))

        flash('Usuário ou senha inválidos.', 'error')

    return render_template('admin_login.html')


@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_username', None)
    flash('Logout realizado.', 'success')
    return redirect(url_for('index'))


@app.route('/health')
def healthcheck():
    """Healthcheck para monitorar app e conexão com banco."""
    conexao_bd = None
    cursor = None
    try:
        conexao_bd = conexao.conectar_bd()
        cursor = conexao_bd.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return jsonify({"status": "ok", "database": "up"}), 200
    except Exception as e:
        return jsonify({"status": "degraded", "database": "down", "error": str(e)}), 503
    finally:
        if cursor:
            cursor.close()
        if conexao_bd:
            conexao_bd.close()

@app.route('/cadastrar_torneio', methods=['GET', 'POST'])
@admin_required
def cadastrar_torneio():
    """Página para cadastrar torneios"""
    if request.method == 'POST':
        try:
            nome = request.form['nome_torneio'].strip()
            rodadas = int(request.form['rodadas'])
            duelistas = int(request.form['duelistas'])
            data = request.form['data'].strip()

            if not nome or not data:
                flash('O nome do torneio e a data não podem estar vazios.', 'error')
                return render_template('cadastrar_torneio.html')
            
            if rodadas <= 0 or duelistas <= 0:
                flash('Os valores de rodadas e duelistas devem ser positivos.', 'error')
                return render_template('cadastrar_torneio.html')

            torneio = Torneio(nome, rodadas, duelistas, data)
            torneio_id = conexao.cadastrar_torneio(torneio)
            flash('Torneio cadastrado com sucesso!', 'success')
            return redirect(url_for('painel_torneio', id=torneio_id))

        except ValueError as e:
            flash(f'Erro: {str(e)}', 'error')
            return render_template('cadastrar_torneio.html')
    
    return render_template('cadastrar_torneio.html')

@app.route('/buscar_duelista', methods=['GET', 'POST'])
@admin_required
def buscar_duelista():
    """Página para buscar duelista específico"""
    duelistas = conexao.carregar_duelistas(incluir_inativos=True)
    status_filtro = 'todos'

    if request.method == 'POST':
        status_filtro = request.form.get('status_filtro', 'todos')

    if status_filtro == 'ativos':
        duelistas = [d for d in duelistas if d.ativo == 1]
    elif status_filtro == 'inativos':
        duelistas = [d for d in duelistas if d.ativo == 0]

    duelistas_ordenados = ordenar_duelistas_para_rank(duelistas)
    duelistas_ordenados = sorted(duelistas_ordenados, key=lambda d: d.ativo, reverse=True)
    
    duelista_encontrado = None
    posicao_encontrada = None
    
    if request.method == 'POST':
        nome_busca = request.form['nome_busca'].strip()
        if nome_busca:
            for posicao, duelista in enumerate(duelistas_ordenados, start=1):
                if nome_busca.casefold() == duelista.nome.casefold():
                    duelista_encontrado = duelista
                    posicao_encontrada = posicao
                    break
            
            if not duelista_encontrado:
                flash('Duelista não encontrado!', 'error')
    
    return render_template('buscar_duelista.html', 
                         duelistas=duelistas_ordenados, 
                         duelista_encontrado=duelista_encontrado,
                         posicao_encontrada=posicao_encontrada,
                         status_filtro=status_filtro)

@app.route('/alterar_duelista/<nome>', methods=['GET', 'POST'])
@admin_required
def alterar_duelista(nome):
    """Página para alterar dados de um duelista"""
    lista_duelistas = conexao.carregar_duelistas()
    duelista = None
    
    for d in lista_duelistas:
        if d.nome.casefold() == nome.casefold():
            duelista = d
            break
    
    if not duelista:
        flash('Duelista não encontrado!', 'error')
        return redirect(url_for('buscar_duelista'))
    
    if request.method == 'POST':
        try:
            novo_nome = request.form['nome'].strip()
            vitorias = int(request.form['vitorias'])
            derrotas = int(request.form['derrotas'])
            empates = int(request.form['empates'])

            if not novo_nome:
                flash('O nome do duelista não pode estar vazio.', 'error')
                return render_template('alterar_duelista.html', duelista=duelista)
            
            if vitorias < 0 or derrotas < 0 or empates < 0:
                flash('Os valores de vitórias, derrotas e empates devem ser não negativos.', 'error')
                return render_template('alterar_duelista.html', duelista=duelista)

            # Atualiza os dados do duelista
            nome_antigo = duelista.nome
            duelista.nome = novo_nome
            duelista.vitorias = vitorias
            duelista.derrotas = derrotas
            duelista.empates = empates

            # Atualiza o banco de dados
            conexao.atualizar_registro_duelista(nome_antigo, novo_nome, vitorias, derrotas, empates, duelista.pontos)
            flash('Dados do duelista atualizados com sucesso!', 'success')
            return redirect(url_for('buscar_duelista'))

        except ValueError as e:
            flash(f'Erro: {str(e)}', 'error')
            return render_template('alterar_duelista.html', duelista=duelista)
    
    return render_template('alterar_duelista.html', duelista=duelista)

@app.route('/ranking')
def ranking():
    """Página com o ranking dos duelistas"""
    try:
        duelistas = conexao.carregar_duelistas()
        duelistas_ordenados = ordenar_duelistas_para_rank(duelistas)
    except Exception:
        duelistas_ordenados = []
        flash('Não foi possível carregar o ranking agora. Verifique a conexão com o banco e tente novamente.', 'error')
    return render_template('ranking.html', duelistas=duelistas_ordenados)


@app.route('/dashboard')
def dashboard_estatisticas():
    """Página com métricas avançadas dos duelistas."""
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
        flash('Não foi possível carregar o dashboard agora. Verifique a conexão com o banco e tente novamente.', 'error')

    return render_template('dashboard_estatisticas.html', dashboard=dados_dashboard)


@app.route('/dashboard/duelista/<path:nome>')
def dashboard_duelista(nome):
    """Dashboard específico com estatísticas detalhadas de um duelista."""
    try:
        dados_duelista = conexao.obter_estatisticas_duelista(nome)
    except Exception:
        dados_duelista = None
        flash('Não foi possível carregar as estatísticas deste duelista agora.', 'error')

    if not dados_duelista:
        flash('Duelista não encontrado para visualização de estatísticas.', 'error')
        return redirect(url_for('dashboard_estatisticas'))

    return render_template('dashboard_duelista.html', dados=dados_duelista)

@app.route('/visualizar_torneios')
def visualizar_torneios():
    """Página para visualizar torneios (buscando do BD)"""
    torneios_bd = conexao.listar_torneios()
    return render_template('visualizar_torneios.html', torneios=torneios_bd)

@app.route('/torneio/<int:id>')
def painel_torneio(id):
    """Página de gerenciamento de um torneio específico"""
    torneio = conexao.get_torneio(id)
    if not torneio:
        flash('Torneio não encontrado!', 'error')
        return redirect(url_for('visualizar_torneios'))
        
    participantes = conexao.listar_participantes_torneio(id)
    todos_duelistas = conexao.carregar_duelistas()
    return render_template('painel_torneio.html', torneio=torneio, participantes=participantes, todos_duelistas=todos_duelistas)

@app.route('/torneio/<int:id>/adicionar_jogador', methods=['POST'])
@admin_required
def adicionar_jogador_torneio(id):
    """Rota invisível para processar a adição de um jogador ao torneio"""
    nome = request.form['nome_duelista'].strip()
    vitorias = int(request.form['vitorias'])
    derrotas = int(request.form['derrotas'])
    empates = int(request.form['empates'])
    topou_torneio = request.form.get('topou_torneio') == 'on'

    colocacao_top = None
    if topou_torneio:
        colocacao_top_raw = request.form.get('colocacao_top', '').strip()
        if not colocacao_top_raw:
            flash('Informe a colocação final no Top Cut.', 'error')
            return redirect(url_for('painel_torneio', id=id))
        try:
            colocacao_top = int(colocacao_top_raw)
        except ValueError:
            flash('A colocação do Top Cut deve ser um número inteiro.', 'error')
            return redirect(url_for('painel_torneio', id=id))
    
    if not nome:
        flash('O nome do duelista não pode estar vazio.', 'error')
    elif vitorias < 0 or derrotas < 0 or empates < 0:
        flash('Os valores devem ser não negativos.', 'error')
    elif topou_torneio and colocacao_top is not None and colocacao_top <= 0:
        flash('A colocação do Top Cut deve ser maior que zero.', 'error')
    else:
        try:
            conexao.adicionar_participante_torneio(
                id,
                nome,
                vitorias,
                derrotas,
                empates,
                topou_torneio=topou_torneio,
                colocacao_top=colocacao_top,
            )
            flash(f'Participação de {nome} registrada com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao registrar participante: {str(e)}', 'error')

    return redirect(url_for('painel_torneio', id=id))

@app.route('/desativar_duelista/<nome>', methods=['POST'])
@admin_required
def desativar_duelista(nome):
    """Manda o duelista para lista de inativos (soft-delete)"""
    try:
        conexao.desativar_duelista(nome)
        flash(f'Duelista {nome} foi inativado! Seu histórico permanecerá nos torneios, mas ele ocultado do Ranking atual.', 'success')
    except Exception as e:
        flash(f'Erro ao inativar duelista {nome}: {str(e)}', 'error')
    
    return redirect(url_for('buscar_duelista'))


@app.route('/reativar_duelista/<nome>', methods=['POST'])
@admin_required
def reativar_duelista(nome):
    """Reativa um duelista previamente inativado"""
    try:
        conexao.reativar_duelista(nome)
        flash(f'Duelista {nome} foi reativado e voltou a aparecer no ranking!', 'success')
    except Exception as e:
        flash(f'Erro ao reativar duelista {nome}: {str(e)}', 'error')

    return redirect(url_for('buscar_duelista'))


@app.route('/excluir_duelista_definitivo/<nome>', methods=['POST'])
@admin_required
def excluir_duelista_definitivo(nome):
    """Exclui um duelista permanentemente quando não houver histórico em torneios."""
    try:
        excluido, detalhe = conexao.excluir_duelista_definitivo(nome)

        if excluido:
            flash(f'Duelista {nome} foi excluído definitivamente.', 'success')
        elif detalhe == 'nao_encontrado':
            flash('Duelista não encontrado.', 'error')
        else:
            flash(
                f'Não foi possível excluir {nome}: existem {detalhe} participações no histórico de torneios. '
                'Mantenha-o inativo para preservar o histórico.',
                'error'
            )
    except Exception as e:
        flash(f'Erro ao excluir duelista {nome}: {str(e)}', 'error')

    return redirect(url_for('buscar_duelista'))

@app.route('/excluir_torneio/<int:id>', methods=['POST'])
@admin_required
def excluir_torneio(id):
    """Exclui um torneio"""
    try:
        conexao.excluir_torneio(id)
        flash('Torneio excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir torneio: {str(e)}', 'error')
    
    return redirect(url_for('visualizar_torneios'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)