import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from core.models import Torneio
from web.auth import admin_required, ip_admin_permitido
from web.security import is_safe_redirect_target


def create_admin_blueprint(conexao, ordenar_duelistas_para_rank):
    admin_bp = Blueprint('admin', __name__)

    @admin_bp.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if not ip_admin_permitido():
            flash('Login administrativo bloqueado para este IP.', 'error')
            return redirect(url_for('public.index'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', '')

            if not admin_password:
                flash('ADMIN_PASSWORD nao esta configurada no ambiente de producao.', 'error')
                return render_template('admin_login.html')

            if username == admin_username and password == admin_password:
                session['is_admin'] = True
                session['admin_username'] = admin_username
                flash('Login de administrador realizado com sucesso.', 'success')

                next_url = request.args.get('next') or request.form.get('next')
                if next_url and is_safe_redirect_target(next_url):
                    return redirect(next_url)
                return redirect(url_for('public.index'))

            flash('Usuario ou senha invalidos.', 'error')

        return render_template('admin_login.html')

    @admin_bp.route('/admin/logout', methods=['POST'])
    def admin_logout():
        session.pop('is_admin', None)
        session.pop('admin_username', None)
        flash('Logout realizado.', 'success')
        return redirect(url_for('public.index'))

    @admin_bp.route('/cadastrar_torneio', methods=['GET', 'POST'])
    @admin_required
    def cadastrar_torneio():
        if request.method == 'POST':
            try:
                nome = request.form['nome_torneio'].strip()
                rodadas = int(request.form['rodadas'])
                duelistas = int(request.form['duelistas'])
                data = request.form['data'].strip()

                if not nome or not data:
                    flash('O nome do torneio e a data nao podem estar vazios.', 'error')
                    return render_template('cadastrar_torneio.html')

                if rodadas <= 0 or duelistas <= 0:
                    flash('Os valores de rodadas e duelistas devem ser positivos.', 'error')
                    return render_template('cadastrar_torneio.html')

                torneio = Torneio(nome, rodadas, duelistas, data)
                torneio_id = conexao.cadastrar_torneio(torneio)
                flash('Torneio cadastrado com sucesso!', 'success')
                return redirect(url_for('public.painel_torneio', id=torneio_id))

            except ValueError as e:
                flash(f'Erro: {str(e)}', 'error')
                return render_template('cadastrar_torneio.html')

        return render_template('cadastrar_torneio.html')

    @admin_bp.route('/buscar_duelista', methods=['GET', 'POST'])
    @admin_required
    def buscar_duelista():
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
                    flash('Duelista nao encontrado!', 'error')

        return render_template(
            'buscar_duelista.html',
            duelistas=duelistas_ordenados,
            duelista_encontrado=duelista_encontrado,
            posicao_encontrada=posicao_encontrada,
            status_filtro=status_filtro,
        )

    @admin_bp.route('/alterar_duelista/<nome>', methods=['GET', 'POST'])
    @admin_required
    def alterar_duelista(nome):
        lista_duelistas = conexao.carregar_duelistas()
        duelista = None

        for d in lista_duelistas:
            if d.nome.casefold() == nome.casefold():
                duelista = d
                break

        if not duelista:
            flash('Duelista nao encontrado!', 'error')
            return redirect(url_for('admin.buscar_duelista'))

        if request.method == 'POST':
            try:
                novo_nome = request.form['nome'].strip()
                vitorias = int(request.form['vitorias'])
                derrotas = int(request.form['derrotas'])
                empates = int(request.form['empates'])

                if not novo_nome:
                    flash('O nome do duelista nao pode estar vazio.', 'error')
                    return render_template('alterar_duelista.html', duelista=duelista)

                if vitorias < 0 or derrotas < 0 or empates < 0:
                    flash('Os valores de vitorias, derrotas e empates devem ser nao negativos.', 'error')
                    return render_template('alterar_duelista.html', duelista=duelista)

                nome_antigo = duelista.nome
                duelista.nome = novo_nome
                duelista.vitorias = vitorias
                duelista.derrotas = derrotas
                duelista.empates = empates

                conexao.atualizar_registro_duelista(
                    nome_antigo,
                    novo_nome,
                    vitorias,
                    derrotas,
                    empates,
                    duelista.pontos,
                )
                flash('Dados do duelista atualizados com sucesso!', 'success')
                return redirect(url_for('admin.buscar_duelista'))

            except ValueError as e:
                flash(f'Erro: {str(e)}', 'error')
                return render_template('alterar_duelista.html', duelista=duelista)

        return render_template('alterar_duelista.html', duelista=duelista)

    @admin_bp.route('/torneio/<int:id>/adicionar_jogador', methods=['POST'])
    @admin_required
    def adicionar_jogador_torneio(id):
        nome = request.form['nome_duelista'].strip()
        try:
            vitorias = int(request.form['vitorias'])
            derrotas = int(request.form['derrotas'])
            empates = int(request.form['empates'])
        except (TypeError, ValueError):
            flash('Vitorias, derrotas e empates devem ser numeros inteiros validos.', 'error')
            return redirect(url_for('public.painel_torneio', id=id))

        topou_torneio = request.form.get('topou_torneio') == 'on'

        colocacao_top = None
        if topou_torneio:
            colocacao_top_raw = request.form.get('colocacao_top', '').strip()
            if not colocacao_top_raw:
                flash('Informe a colocacao final no Top Cut.', 'error')
                return redirect(url_for('public.painel_torneio', id=id))
            try:
                colocacao_top = int(colocacao_top_raw)
            except ValueError:
                flash('A colocacao do Top Cut deve ser um numero inteiro.', 'error')
                return redirect(url_for('public.painel_torneio', id=id))

        if not nome:
            flash('O nome do duelista nao pode estar vazio.', 'error')
        elif vitorias < 0 or derrotas < 0 or empates < 0:
            flash('Os valores devem ser nao negativos.', 'error')
        elif topou_torneio and colocacao_top is not None and colocacao_top <= 0:
            flash('A colocacao do Top Cut deve ser maior que zero.', 'error')
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
                flash(f'Participacao de {nome} registrada com sucesso!', 'success')
            except Exception as e:
                flash(f'Erro ao registrar participante: {str(e)}', 'error')

        return redirect(url_for('public.painel_torneio', id=id))

    @admin_bp.route('/desativar_duelista/<nome>', methods=['POST'])
    @admin_required
    def desativar_duelista(nome):
        try:
            conexao.desativar_duelista(nome)
            flash(
                f'Duelista {nome} foi inativado! Seu historico permanecera nos torneios, mas ele ocultado do Ranking atual.',
                'success',
            )
        except Exception as e:
            flash(f'Erro ao inativar duelista {nome}: {str(e)}', 'error')

        return redirect(url_for('admin.buscar_duelista'))

    @admin_bp.route('/reativar_duelista/<nome>', methods=['POST'])
    @admin_required
    def reativar_duelista(nome):
        try:
            conexao.reativar_duelista(nome)
            flash(f'Duelista {nome} foi reativado e voltou a aparecer no ranking!', 'success')
        except Exception as e:
            flash(f'Erro ao reativar duelista {nome}: {str(e)}', 'error')

        return redirect(url_for('admin.buscar_duelista'))

    @admin_bp.route('/excluir_duelista_definitivo/<nome>', methods=['POST'])
    @admin_required
    def excluir_duelista_definitivo(nome):
        try:
            excluido, detalhe = conexao.excluir_duelista_definitivo(nome)

            if excluido:
                flash(f'Duelista {nome} foi excluido definitivamente.', 'success')
            elif detalhe == 'nao_encontrado':
                flash('Duelista nao encontrado.', 'error')
            else:
                flash(
                    f'Nao foi possivel excluir {nome}: existem {detalhe} participacoes no historico de torneios. '
                    'Mantenha-o inativo para preservar o historico.',
                    'error',
                )
        except Exception as e:
            flash(f'Erro ao excluir duelista {nome}: {str(e)}', 'error')

        return redirect(url_for('admin.buscar_duelista'))

    @admin_bp.route('/excluir_torneio/<int:id>', methods=['POST'])
    @admin_required
    def excluir_torneio(id):
        try:
            conexao.excluir_torneio(id)
            flash('Torneio excluido com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao excluir torneio: {str(e)}', 'error')

        return redirect(url_for('public.visualizar_torneios'))

    return admin_bp
