from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from web.auth import admin_required, ip_admin_permitido
from web.security import is_safe_redirect_target
from web.services.admin_service import AdminService


def create_admin_blueprint(conexao, ordenar_duelistas_para_rank):
    admin_bp = Blueprint('admin', __name__)
    admin_service = AdminService(conexao, ordenar_duelistas_para_rank)

    @admin_bp.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if not ip_admin_permitido():
            flash('Login administrativo bloqueado para este IP.', 'error')
            return redirect(url_for('public.index'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            autenticado, mensagem = admin_service.autenticar_admin(username, password)
            if autenticado:
                session['is_admin'] = True
                session['admin_username'] = username
                flash('Login de administrador realizado com sucesso.', 'success')

                next_url = request.args.get('next') or request.form.get('next')
                if next_url and is_safe_redirect_target(next_url):
                    return redirect(next_url)
                return redirect(url_for('public.index'))

            flash(mensagem, 'error')

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
            ok, torneio_id, mensagem = admin_service.cadastrar_torneio(
                request.form['nome_torneio'].strip(),
                request.form.get('rodadas'),
                request.form.get('duelistas'),
                request.form['data'].strip(),
            )

            if ok:
                flash('Torneio cadastrado com sucesso!', 'success')
                return redirect(url_for('public.painel_torneio', id=torneio_id))

            flash(mensagem, 'error')
            return render_template('cadastrar_torneio.html')

        return render_template('cadastrar_torneio.html')

    @admin_bp.route('/buscar_duelista', methods=['GET', 'POST'])
    @admin_required
    def buscar_duelista():
        status_filtro = 'todos'
        nome_busca = ''

        if request.method == 'POST':
            status_filtro = request.form.get('status_filtro', 'todos')
            nome_busca = request.form['nome_busca'].strip()

        resultado = admin_service.buscar_duelistas(status_filtro=status_filtro, nome_busca=nome_busca)

        if request.method == 'POST' and nome_busca and not resultado['duelista_encontrado']:
            flash('Duelista nao encontrado!', 'error')

        return render_template(
            'buscar_duelista.html',
            duelistas=resultado['duelistas'],
            duelista_encontrado=resultado['duelista_encontrado'],
            posicao_encontrada=resultado['posicao_encontrada'],
            status_filtro=resultado['status_filtro'],
        )

    @admin_bp.route('/alterar_duelista/<nome>', methods=['GET', 'POST'])
    @admin_required
    def alterar_duelista(nome):
        duelista = admin_service.obter_duelista_por_nome(nome)

        if not duelista:
            flash('Duelista nao encontrado!', 'error')
            return redirect(url_for('admin.buscar_duelista'))

        if request.method == 'POST':
            ok, mensagem = admin_service.atualizar_duelista(
                duelista,
                request.form['nome'].strip(),
                request.form.get('vitorias'),
                request.form.get('derrotas'),
                request.form.get('empates'),
            )
            if ok:
                flash(mensagem, 'success')
                return redirect(url_for('admin.buscar_duelista'))

            flash(mensagem, 'error')
            return render_template('alterar_duelista.html', duelista=duelista)

        return render_template('alterar_duelista.html', duelista=duelista)

    @admin_bp.route('/torneio/<int:id>/adicionar_jogador', methods=['POST'])
    @admin_required
    def adicionar_jogador_torneio(id):
        nome = request.form['nome_duelista'].strip()
        topou_torneio = request.form.get('topou_torneio') == 'on'
        ok, payload, mensagem = admin_service.validar_payload_participacao(
            nome,
            request.form.get('vitorias'),
            request.form.get('derrotas'),
            request.form.get('empates'),
            topou_torneio,
            request.form.get('colocacao_top', '').strip(),
        )

        if not ok:
            flash(mensagem, 'error')
            return redirect(url_for('public.painel_torneio', id=id))

        try:
            sucesso_msg = admin_service.registrar_participacao(id, payload)
            flash(sucesso_msg, 'success')
        except Exception as e:
            flash(f'Erro ao registrar participante: {str(e)}', 'error')

        return redirect(url_for('public.painel_torneio', id=id))

    @admin_bp.route('/desativar_duelista/<nome>', methods=['POST'])
    @admin_required
    def desativar_duelista(nome):
        try:
            flash(admin_service.desativar_duelista(nome), 'success')
        except Exception as e:
            flash(f'Erro ao inativar duelista {nome}: {str(e)}', 'error')

        return redirect(url_for('admin.buscar_duelista'))

    @admin_bp.route('/reativar_duelista/<nome>', methods=['POST'])
    @admin_required
    def reativar_duelista(nome):
        try:
            flash(admin_service.reativar_duelista(nome), 'success')
        except Exception as e:
            flash(f'Erro ao reativar duelista {nome}: {str(e)}', 'error')

        return redirect(url_for('admin.buscar_duelista'))

    @admin_bp.route('/excluir_duelista_definitivo/<nome>', methods=['POST'])
    @admin_required
    def excluir_duelista_definitivo(nome):
        try:
            excluido, mensagem = admin_service.excluir_duelista_definitivo(nome)
            if excluido:
                flash(mensagem, 'success')
            else:
                flash(mensagem, 'error')
        except Exception as e:
            flash(f'Erro ao excluir duelista {nome}: {str(e)}', 'error')

        return redirect(url_for('admin.buscar_duelista'))

    @admin_bp.route('/excluir_torneio/<int:id>', methods=['POST'])
    @admin_required
    def excluir_torneio(id):
        try:
            flash(admin_service.excluir_torneio(id), 'success')
        except Exception as e:
            flash(f'Erro ao excluir torneio: {str(e)}', 'error')

        return redirect(url_for('public.visualizar_torneios'))

    return admin_bp
