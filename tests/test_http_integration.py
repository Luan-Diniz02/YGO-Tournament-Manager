import importlib
import re

import pytest

from web.services.admin_service import AdminService


def _extrair_csrf(html):
    match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def _login_admin(client):
    page = client.get('/admin/login')
    csrf = _extrair_csrf(page.get_data(as_text=True))
    return client.post(
        '/admin/login',
        data={
            '_csrf_token': csrf,
            'username': 'admin',
            'password': 'senha-forte',
        },
        follow_redirects=False,
    )


def _csrf_da_home(client):
    home = client.get('/')
    return _extrair_csrf(home.get_data(as_text=True))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('FLASK_SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('AUTO_INIT_DB', '0')
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'senha-forte')

    import web.app as app_module

    app_module = importlib.reload(app_module)
    app = app_module.app
    app.config.update(TESTING=True)

    return app.test_client()


def test_home_deve_retornar_200(client):
    resp = client.get('/')

    assert resp.status_code == 200


def test_rota_admin_sem_login_redireciona_para_login(client):
    resp = client.get('/cadastrar_torneio', follow_redirects=False)

    assert resp.status_code == 302
    assert '/admin/login' in resp.headers['Location']


def test_login_sem_csrf_e_bloqueado(client):
    resp = client.post(
        '/admin/login',
        data={'username': 'admin', 'password': 'senha-forte'},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')


def test_login_com_csrf_e_credencial_invalida(client):
    page = client.get('/admin/login')
    csrf = _extrair_csrf(page.get_data(as_text=True))

    resp = client.post(
        '/admin/login',
        data={
            '_csrf_token': csrf,
            'username': 'admin',
            'password': 'senha-errada',
        },
        follow_redirects=True,
    )

    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'Usuario ou senha invalidos.' in body


def test_login_sucesso_ignora_next_externo(client):
    page = client.get('/admin/login?next=https://evil.example/phishing')
    csrf = _extrair_csrf(page.get_data(as_text=True))

    resp = client.post(
        '/admin/login?next=https://evil.example/phishing',
        data={
            '_csrf_token': csrf,
            'username': 'admin',
            'password': 'senha-forte',
            'next': 'https://evil.example/phishing',
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')


def test_login_sucesso_com_next_interno_redireciona(client):
    page = client.get('/admin/login?next=/cadastrar_torneio')
    csrf = _extrair_csrf(page.get_data(as_text=True))

    resp = client.post(
        '/admin/login?next=/cadastrar_torneio',
        data={
            '_csrf_token': csrf,
            'username': 'admin',
            'password': 'senha-forte',
            'next': '/cadastrar_torneio',
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/cadastrar_torneio')


def test_logout_sem_csrf_e_bloqueado(client):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    resp = client.post('/admin/logout', follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')

    # Ainda deve estar autenticado, pois logout sem CSRF não é processado.
    acesso_admin = client.get('/cadastrar_torneio', follow_redirects=False)
    assert acesso_admin.status_code == 200


def test_logout_com_csrf_remove_sessao(client):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    home = client.get('/')
    csrf = _extrair_csrf(home.get_data(as_text=True))

    resp = client.post('/admin/logout', data={'_csrf_token': csrf}, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')

    # Após logout real, deve voltar a bloquear rota admin.
    acesso_admin = client.get('/cadastrar_torneio', follow_redirects=False)
    assert acesso_admin.status_code == 302
    assert '/admin/login' in acesso_admin.headers['Location']


def test_cadastrar_torneio_autenticado_sucesso_com_service_mockado(client, monkeypatch):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    def _mock_cadastrar(self, nome, rodadas_raw, duelistas_raw, data):
        return True, 777, 'Torneio cadastrado com sucesso!'

    monkeypatch.setattr(AdminService, 'cadastrar_torneio', _mock_cadastrar)

    page = client.get('/cadastrar_torneio')
    csrf = _extrair_csrf(page.get_data(as_text=True))

    resp = client.post(
        '/cadastrar_torneio',
        data={
            '_csrf_token': csrf,
            'nome_torneio': 'Etapa Mockada',
            'rodadas': '4',
            'duelistas': '16',
            'data': '2026-03-25',
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/torneio/777')


def test_cadastrar_torneio_autenticado_falha_com_service_mockado(client, monkeypatch):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    def _mock_cadastrar(self, nome, rodadas_raw, duelistas_raw, data):
        return False, None, 'Os valores de rodadas e duelistas devem ser positivos.'

    monkeypatch.setattr(AdminService, 'cadastrar_torneio', _mock_cadastrar)

    page = client.get('/cadastrar_torneio')
    csrf = _extrair_csrf(page.get_data(as_text=True))

    resp = client.post(
        '/cadastrar_torneio',
        data={
            '_csrf_token': csrf,
            'nome_torneio': 'Etapa Mockada',
            'rodadas': '0',
            'duelistas': '0',
            'data': '2026-03-25',
        },
        follow_redirects=True,
    )

    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'Os valores de rodadas e duelistas devem ser positivos.' in body


def test_desativar_duelista_com_csrf_chama_service(client, monkeypatch):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    chamadas = {'nome': None}

    def _mock_desativar(self, nome):
        chamadas['nome'] = nome
        return 'Duelista Yugi foi inativado!'

    monkeypatch.setattr(AdminService, 'desativar_duelista', _mock_desativar)

    resp = client.post(
        '/desativar_duelista/Yugi',
        data={'_csrf_token': _csrf_da_home(client)},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/buscar_duelista')
    assert chamadas['nome'] == 'Yugi'


def test_reativar_duelista_com_csrf_chama_service(client, monkeypatch):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    chamadas = {'nome': None}

    def _mock_reativar(self, nome):
        chamadas['nome'] = nome
        return 'Duelista Kaiba foi reativado!'

    monkeypatch.setattr(AdminService, 'reativar_duelista', _mock_reativar)

    resp = client.post(
        '/reativar_duelista/Kaiba',
        data={'_csrf_token': _csrf_da_home(client)},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/buscar_duelista')
    assert chamadas['nome'] == 'Kaiba'


def test_excluir_duelista_definitivo_com_csrf_chama_service(client, monkeypatch):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    chamadas = {'nome': None}

    def _mock_excluir_definitivo(self, nome):
        chamadas['nome'] = nome
        return False, 'Nao foi possivel excluir.'

    monkeypatch.setattr(AdminService, 'excluir_duelista_definitivo', _mock_excluir_definitivo)

    resp = client.post(
        '/excluir_duelista_definitivo/Joey',
        data={'_csrf_token': _csrf_da_home(client)},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/buscar_duelista')
    assert chamadas['nome'] == 'Joey'


def test_excluir_torneio_com_csrf_chama_service(client, monkeypatch):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    chamadas = {'id': None}

    def _mock_excluir_torneio(self, torneio_id):
        chamadas['id'] = torneio_id
        return 'Torneio excluido com sucesso!'

    monkeypatch.setattr(AdminService, 'excluir_torneio', _mock_excluir_torneio)

    resp = client.post(
        '/excluir_torneio/55',
        data={'_csrf_token': _csrf_da_home(client)},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/visualizar_torneios')
    assert chamadas['id'] == 55


def test_adicionar_jogador_payload_invalido_nao_registra(client, monkeypatch):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    def _mock_validar(self, nome, vitorias_raw, derrotas_raw, empates_raw, topou_torneio, colocacao_top_raw):
        return False, None, 'Payload invalido.'

    registrar_chamado = {'valor': False}

    def _mock_registrar(self, torneio_id, payload):
        registrar_chamado['valor'] = True
        return 'Nao deveria registrar'

    monkeypatch.setattr(AdminService, 'validar_payload_participacao', _mock_validar)
    monkeypatch.setattr(AdminService, 'registrar_participacao', _mock_registrar)

    resp = client.post(
        '/torneio/7/adicionar_jogador',
        data={
            '_csrf_token': _csrf_da_home(client),
            'nome_duelista': 'Yugi',
            'vitorias': '1',
            'derrotas': '0',
            'empates': '0',
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/torneio/7')
    assert registrar_chamado['valor'] is False
