import importlib
import re

import pytest

from web.services.admin_service import AdminService
from web.services.public_service import PublicService


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

    def _mock_cadastrar(self, nome, rodadas_raw, duelistas_raw, data, temporada_id=None):
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

    def _mock_cadastrar(self, nome, rodadas_raw, duelistas_raw, data, temporada_id=None):
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


def test_dashboard_estatisticas_conversao_travessao_quando_zero_tops(client, monkeypatch):
    mock_dashboard = {
        'resumo': {
            'total_duelistas': 2,
            'total_partidas': 10,
            'total_vitorias': 5,
            'total_derrotas': 5,
            'total_empates': 0,
            'total_tops': 2,
            'total_campeonatos': 1,
            'win_rate_geral': 50.0,
            'taxa_conversao_top_titulo_geral': 50.0,
            'min_participacoes_win_rate': 1,
        },
        'lideres': {
            'maior_win_rate': None,
            'mais_tops': None,
            'mais_campeonatos': None,
        },
        'duelistas': [
            {
                'posicao_ranking': 1,
                'nome': 'Yugi',
                'pontos': 20,
                'vitorias': 8,
                'derrotas': 2,
                'empates': 0,
                'partidas': 10,
                'win_rate': 80.0,
                'participacao': 2,
                'tops': 2,
                'campeonatos': 1,
                'taxa_conversao_top_titulo': 50.0,
            },
            {
                'posicao_ranking': 2,
                'nome': 'Joey',
                'pontos': 5,
                'vitorias': 2,
                'derrotas': 8,
                'empates': 0,
                'partidas': 10,
                'win_rate': 20.0,
                'participacao': 2,
                'tops': 0,
                'campeonatos': 0,
                'taxa_conversao_top_titulo': 0.0,
            },
            {
                'posicao_ranking': 3,
                'nome': 'Kaiba',
                'pontos': 10,
                'vitorias': 5,
                'derrotas': 5,
                'empates': 0,
                'partidas': 10,
                'win_rate': 50.0,
                'participacao': 2,
                'tops': 1,
                'campeonatos': 0,
                'taxa_conversao_top_titulo': 0.0,
            },
        ],
    }

    monkeypatch.setattr(PublicService, 'carregar_dashboard', lambda self, *args, **kwargs: mock_dashboard)
    monkeypatch.setattr(PublicService, 'listar_temporadas', lambda self: [])
    monkeypatch.setattr(PublicService, 'obter_temporada_ativa', lambda self: None)

    resp = client.get('/dashboard')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Joey (tops=0): não deve exibir a barra de conversão nem 0.0% na tabela desktop
    # Yugi (tops=2): deve exibir 50.0% e a barra de conversão
    # Kaiba (tops=1, titulos=0): deve exibir 0.0% e a barra de conversão, pois topou
    assert '50.0%' in html
    assert 'title="1 título(s) em 2 Top Cut(s)"' in html
    assert 'title="0 título(s) em 1 Top Cut(s)"' in html
    assert 'title="0 título(s) em 0 Top Cut(s)"' not in html


def test_dashboard_duelista_conversao_travessao_quando_zero_tops(client, monkeypatch):
    def mock_carregar_duelista(self, nome, *args, **kwargs):
        if nome == 'SemTops':
            return {
                'duelista': {'nome': 'SemTops', 'ativo': 1, 'pontos': 5, 'vitorias': 2, 'derrotas': 4, 'empates': 0, 'participacao': 2},
                'resumo': {'partidas_total': 6, 'win_rate_geral': 33.3, 'tops': 0, 'campeonatos': 0, 'taxa_conversao_top_titulo': 0.0, 'qtd_torneios_historico': 2},
                'conquistas': [],
                'historico': [],
            }
        return {
            'duelista': {'nome': 'ComTops', 'ativo': 1, 'pontos': 20, 'vitorias': 8, 'derrotas': 2, 'empates': 0, 'participacao': 2},
            'resumo': {'partidas_total': 10, 'win_rate_geral': 80.0, 'tops': 2, 'campeonatos': 1, 'taxa_conversao_top_titulo': 50.0, 'qtd_torneios_historico': 2},
            'conquistas': [],
            'historico': [],
        }

    monkeypatch.setattr(PublicService, 'carregar_dashboard_duelista', mock_carregar_duelista)
    monkeypatch.setattr(PublicService, 'listar_temporadas', lambda self: [])
    monkeypatch.setattr(PublicService, 'obter_temporada_ativa', lambda self: None)

    # Duelista com 0 tops: conversão deve ser &mdash; e não '0.0%'
    resp_sem_tops = client.get('/dashboard/duelista/SemTops')
    assert resp_sem_tops.status_code == 200
    html_sem = resp_sem_tops.get_data(as_text=True)
    assert '0.0%' not in html_sem
    assert '<div class="fs-4 fw-bold text-muted mt-1">&mdash;</div>' in html_sem

    # Duelista com tops > 0: conversão deve ser exibida com %
    resp_com_tops = client.get('/dashboard/duelista/ComTops')
    assert resp_com_tops.status_code == 200
    html_com = resp_com_tops.get_data(as_text=True)
    assert '<div class="fs-4 fw-bold text-dark mt-1">50.0%</div>' in html_com


def test_dashboard_duelista_graficos_e_posicao_mobile(client, monkeypatch):
    mock_dados = {
        'duelista': {'nome': 'Yugi Muto', 'ativo': 1, 'pontos': 25, 'vitorias': 9, 'derrotas': 3, 'empates': 0, 'participacao': 2},
        'resumo': {'partidas_total': 12, 'win_rate_geral': 75.0, 'tops': 2, 'campeonatos': 1, 'taxa_conversao_top_titulo': 50.0, 'qtd_torneios_historico': 2},
        'conquistas': [],
        'historico': [
            {
                'torneio_id': 1,
                'torneio_nome': 'Torneio Mensal - Agosto',
                'torneio_data': None,
                'vitorias': 5,
                'derrotas': 1,
                'empates': 0,
                'rodadas': 4,
                'posicao_geral': 1,
                'topou_torneio': True,
                'pontos_obtidos': 16,
            }
        ],
    }
    monkeypatch.setattr(PublicService, 'carregar_dashboard_duelista', lambda self, *args, **kwargs: mock_dados)
    monkeypatch.setattr(PublicService, 'listar_temporadas', lambda self: [])
    monkeypatch.setattr(PublicService, 'obter_temporada_ativa', lambda self: None)

    resp = client.get('/dashboard/duelista/Yugi%20Muto')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # 1. Porcentagem no gráfico de distribuição (legenda e tooltip, centro limpo)
    assert 'doughnutCenterText' not in html
    assert 'formatPct' in html

    # 2. Intervalo de 3 no gráfico de evolução
    assert 'stepSize: 3' in html

    # 3. Número da posição à esquerda de TOP no histórico
    pos_num = html.find('1º')
    pos_top = html.find('>TOP</span>', pos_num)
    assert pos_num != -1 and pos_top != -1 and pos_num < pos_top

    # 4. Modo mobile centralizado
    assert '<div class="mobile-stat-item text-center">' in html


def test_index_home_resumo_vivo_da_liga(client, monkeypatch):
    mock_resumo = {
        'temporada_ativa': {'id': 2, 'nome': 'Temporada 2 - 2026', 'data_inicio': None, 'data_fim': None},
        'metricas': {'total_torneios': 5, 'total_duelistas': 16, 'total_partidas': 60},
        'lider': {'nome': 'Seto Kaiba', 'pontos': 45, 'win_rate': 85.0, 'campeonatos': 2, 'tops': 3},
        'ultimo_torneio': {
            'id': 10,
            'nome': 'Torneio Mensal - Agosto',
            'data': None,
            'qtd_participantes': 8,
            'campeao_nome': 'Seto Kaiba',
            'campeao_vitorias': 4,
            'campeao_derrotas': 0,
        },
    }
    monkeypatch.setattr(PublicService, 'obter_resumo_home', lambda self: mock_resumo)

    resp = client.get('/')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Métricas
    assert '5</div>' in html
    assert '16</div>' in html
    assert '60</div>' in html

    # Destaque Líder
    assert 'Líder da Liga' in html
    assert 'Seto Kaiba' in html
    assert '45 pts' in html
    assert '85.0% WR' in html

    # Destaque Último Torneio
    assert 'Último Torneio' in html
    assert 'Torneio Mensal - Agosto' in html
    assert 'Seto Kaiba' in html
    assert '4V / 0D' in html

    # CTA focado na temporada ativa sem botões redundantes no Hero
    assert 'Ranking da Temporada' in html
    assert 'Ver Torneios' not in html


def test_index_home_sem_temporada_ativa(client, monkeypatch):
    mock_resumo = {
        'temporada_ativa': None,
        'metricas': {'total_torneios': 0, 'total_duelistas': 0, 'total_partidas': 0},
        'lider': None,
        'ultimo_torneio': None,
    }
    monkeypatch.setattr(PublicService, 'obter_resumo_home', lambda self: mock_resumo)

    resp = client.get('/')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert 'Nenhuma temporada ativa no momento' in html
    assert 'Ver Ranking Geral' in html
    assert 'Temporada em aberto' in html
    assert 'Nenhum torneio recente' in html


def test_telas_modernizadas_sem_coluna_empates(client, monkeypatch):
    # 1. Testar que /dashboard não exibe "+ Empates +" na fórmula
    mock_dashboard = {
        'resumo': {'total_duelistas': 0, 'total_partidas': 0, 'total_vitorias': 0, 'total_derrotas': 0, 'total_empates': 0, 'total_tops': 0, 'total_campeonatos': 0, 'win_rate_geral': 0.0, 'taxa_conversao_top_titulo_geral': 0.0, 'min_participacoes_win_rate': 1},
        'lideres': {'maior_win_rate': None, 'mais_tops': None, 'mais_campeonatos': None},
        'duelistas': [],
    }
    monkeypatch.setattr(PublicService, 'carregar_dashboard', lambda self, *args, **kwargs: mock_dashboard)
    monkeypatch.setattr(PublicService, 'listar_temporadas', lambda self: [])
    monkeypatch.setattr(PublicService, 'obter_temporada_ativa', lambda self: None)

    resp_dash = client.get('/dashboard')
    assert resp_dash.status_code == 200
    html_dash = resp_dash.get_data(as_text=True)
    assert '+ Empates +' not in html_dash
    assert 'Pontos = (Vitórias × 3) + Participações' in html_dash

    # 2. Testar que /painel_torneio não exibe coluna 'E' na tabela desktop e formulário admin tem empates hidden
    _login_admin(client)
    mock_painel = {
        'torneio': {'id': 1, 'nome': 'Etapa 1', 'rodadas': 4, 'quant_duelistas': 8, 'data': None},
        'participantes': [],
        'todos_duelistas': [],
    }
    monkeypatch.setattr(PublicService, 'carregar_painel_torneio', lambda self, id: mock_painel)

    resp_torneio = client.get('/torneio/1')
    assert resp_torneio.status_code == 200
    html_torneio = resp_torneio.get_data(as_text=True)
    assert '<th class="text-center">E</th>' not in html_torneio
    assert '<input type="hidden" id="empates" name="empates" value="0">' in html_torneio


def test_dashboard_compartilhar_ranking(client, monkeypatch):
    mock_dashboard = {
        'resumo': {
            'total_duelistas': 3,
            'total_partidas': 15,
            'total_vitorias': 10,
            'total_derrotas': 5,
            'total_empates': 0,
            'total_tops': 3,
            'total_campeonatos': 1,
            'win_rate_geral': 66.7,
            'taxa_conversao_top_titulo_geral': 33.3,
            'min_participacoes_win_rate': 1,
        },
        'lideres': {
            'maior_win_rate': None,
            'mais_tops': None,
            'mais_campeonatos': None,
        },
        'duelistas': [
            {
                'posicao_ranking': 1,
                'nome': 'Yugi Muto',
                'pontos': 30,
                'vitorias': 9,
                'derrotas': 1,
                'empates': 0,
                'partidas': 10,
                'win_rate': 90.0,
                'participacao': 3,
                'tops': 3,
                'campeonatos': 2,
                'taxa_conversao_top_titulo': 66.7,
            },
            {
                'posicao_ranking': 2,
                'nome': 'Seto Kaiba',
                'pontos': 25,
                'vitorias': 7,
                'derrotas': 3,
                'empates': 0,
                'partidas': 10,
                'win_rate': 70.0,
                'participacao': 3,
                'tops': 2,
                'campeonatos': 1,
                'taxa_conversao_top_titulo': 50.0,
            },
            {
                'posicao_ranking': 3,
                'nome': 'Joey Wheeler',
                'pontos': 18,
                'vitorias': 5,
                'derrotas': 5,
                'empates': 0,
                'partidas': 10,
                'win_rate': 50.0,
                'participacao': 3,
                'tops': 1,
                'campeonatos': 0,
                'taxa_conversao_top_titulo': 0.0,
            },
        ],
    }
    temporadas = [{'id': 1, 'nome': 'Temporada 2026', 'ativa': 1}]

    monkeypatch.setattr(PublicService, 'carregar_dashboard', lambda self, *args, **kwargs: mock_dashboard)
    monkeypatch.setattr(PublicService, 'listar_temporadas', lambda self: temporadas)
    monkeypatch.setattr(PublicService, 'obter_temporada_ativa', lambda self: temporadas[0])

    resp = client.get('/dashboard?temporada=1')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # 1. Botão no cabeçalho
    assert 'id="btn-share-ranking"' in html
    assert 'Compartilhar Ranking' in html

    # 2. Modal e Preview Card
    assert 'id="modalShareRanking"' in html
    assert 'modal-dialog-scrollable' in html
    assert 'id="ranking-share-card"' in html
    assert 'Ranking Geral' in html
    assert 'Liga YGO Marabá' in html
    assert 'Temporada 2026' in html
    assert 'TCG Marabá &bull; Ranking Oficial' in html

    # 3. Duelistas renderizados no card
    assert 'Yugi Muto' in html
    assert 'Seto Kaiba' in html
    assert 'Joey Wheeler' in html
    assert '🥇 1º' in html
    assert '🥈 2º' in html
    assert '🥉 3º' in html

    # 4. Botões de ação no modal
    assert 'id="btn-download-share-ranking"' in html
    assert 'Baixar Imagem do Ranking' in html
    assert 'id="btn-share-ranking-action"' in html
    assert 'Compartilhar Imagem' in html

    # 5. Dependência html2canvas e lógica de download/share via YGOUtils
    assert 'html2canvas@1.4.1/dist/html2canvas.min.js' in html
    assert 'ranking-liga-ygo.png' in html
    assert 'YGOUtils.baixarElementoComoImagem' in html
    assert 'YGOUtils.compartilharElementoComoImagem' in html

    js_resp = client.get('/static/js/script.js')
    assert js_resp.status_code == 200
    js = js_resp.get_data(as_text=True)
    assert 'navigator.share' in js
    assert 'api.whatsapp.com/send?text=' in js


def test_dashboard_compartilhar_ranking_com_mais_de_dez_duelistas(client, monkeypatch):
    duelistas = [
        {
            'posicao_ranking': i,
            'nome': f'Duelista {i:02d}',
            'pontos': 50 - i,
            'vitorias': 10,
            'derrotas': 2,
            'empates': 0,
            'partidas': 12,
            'win_rate': 83.3,
            'participacao': 3,
            'tops': 1,
            'campeonatos': 1 if i <= 3 else 0,
            'taxa_conversao_top_titulo': 100.0 if i <= 3 else 0.0,
        }
        for i in range(1, 16)
    ]
    mock_dashboard = {
        'resumo': {
            'total_duelistas': 15,
            'total_partidas': 180,
            'total_vitorias': 90,
            'total_derrotas': 90,
            'total_empates': 0,
            'total_tops': 15,
            'total_campeonatos': 3,
            'win_rate_geral': 50.0,
            'taxa_conversao_top_titulo_geral': 20.0,
            'min_participacoes_win_rate': 1,
        },
        'lideres': {
            'maior_win_rate': None,
            'mais_tops': None,
            'mais_campeonatos': None,
        },
        'duelistas': duelistas,
    }
    temporadas = [{'id': 1, 'nome': 'Temporada 2026', 'ativa': 1}]

    monkeypatch.setattr(PublicService, 'carregar_dashboard', lambda self, *args, **kwargs: mock_dashboard)
    monkeypatch.setattr(PublicService, 'listar_temporadas', lambda self: temporadas)
    monkeypatch.setattr(PublicService, 'obter_temporada_ativa', lambda self: temporadas[0])

    resp = client.get('/dashboard?temporada=1')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Extrai o conteúdo do card compartilhado (#ranking-share-card)
    assert 'id="ranking-share-card"' in html
    card_html = html.split('id="ranking-share-card"')[1].split('id="btn-download-share-ranking"')[0]

    # Garante que todos os 15 duelistas (além do top 10) estão no card
    for i in range(1, 16):
        nome_duelista = f'Duelista {i:02d}'
        assert nome_duelista in card_html, f'{nome_duelista} deve ser renderizado no card de ranking'
        if i == 1:
            assert '🥇 1º' in card_html
        elif i == 2:
            assert '🥈 2º' in card_html
        elif i == 3:
            assert '🥉 3º' in card_html
        else:
            assert f'{i}º' in card_html
def test_modais_confirmacao_admin(client, monkeypatch):
    login_resp = _login_admin(client)
    assert login_resp.status_code == 302

    # Mock de torneios para visualizar_torneios
    torneios_mock = [{
        'id': 10,
        'nome': 'Torneio Teste Modal',
        'rodadas': 4,
        'quant_duelistas': 8,
        'data': None,
        'temporada_id': None,
        'temporada_nome': None,
        'qtd_participantes': 8,
    }]
    monkeypatch.setattr(PublicService, 'listar_torneios', lambda self: torneios_mock)
    monkeypatch.setattr(PublicService, 'listar_temporadas', lambda self: [])

    # 1. Visualizar Torneios - Modal de exclusão
    resp_t = client.get('/visualizar_torneios')
    assert resp_t.status_code == 200
    html_t = resp_t.get_data(as_text=True)
    assert 'id="confirmarExcluirTorneioModal"' in html_t
    assert 'btn-excluir-torneio' in html_t

    # 2. Gerenciar Temporadas - Modais de ativar e excluir (sem onclick confirm)
    temporadas_mock = [{
        'id': 1,
        'nome': 'Temporada 1',
        'data_inicio': None,
        'data_fim': None,
        'ativa': 0,
    }]
    monkeypatch.setattr(AdminService, 'listar_temporadas', lambda self: temporadas_mock)
    resp_temp = client.get('/temporadas')
    assert resp_temp.status_code == 200
    html_temp = resp_temp.get_data(as_text=True)
    assert 'id="confirmarAtivarTemporadaModal"' in html_temp
    assert 'id="confirmarExcluirTemporadaModal"' in html_temp
    assert 'btn-ativar-temporada' in html_temp
    assert 'btn-excluir-temporada' in html_temp
    assert 'onclick="return confirm(' not in html_temp

    # 3. Buscar Duelistas - Modal de exclusão
    duelistas_mock = [{
        'id': 1,
        'nome': 'Duelista Inativo',
        'pontos': 0,
        'vitorias': 0,
        'derrotas': 0,
        'empates': 0,
        'participacao': 0,
        'ativo': 0,
    }]
    monkeypatch.setattr(AdminService, 'buscar_duelistas', lambda self, **kwargs: {
        'duelistas': duelistas_mock,
        'duelista_encontrado': False,
        'posicao_encontrada': None,
        'status_filtro': 'todos',
        'nome_busca': ''
    })
    resp_d = client.get('/buscar_duelista')
    assert resp_d.status_code == 200
    html_d = resp_d.get_data(as_text=True)
    assert 'id="confirmarExcluirDuelistaModal"' in html_d
    assert 'btn-excluir-duelista' in html_d


def test_extrair_filtros_temporada():
    from web.blueprints.public import _extrair_filtros_temporada

    temporadas = [
        {'id': 1, 'nome': 'Temporada 1'},
        {'id': 2, 'nome': 'Temporada 2'},
    ]

    # Caso 1: Sem temporada passada, usa temp_ativa
    tid, di, df, nome = _extrair_filtros_temporada({}, {'id': 1, 'nome': 'Temporada 1'}, temporadas)
    assert tid == 1
    assert di == ''
    assert df == ''
    assert nome == 'Temporada 1'

    # Caso 2: Sem temporada e sem temp_ativa -> geral
    tid, di, df, nome = _extrair_filtros_temporada({}, None, temporadas)
    assert tid == 'geral'
    assert nome == 'Geral (All-time)'

    # Caso 3: Temporada especifica via args com datas
    args = {'temporada': '2', 'data_inicio': '2026-01-01', 'data_fim': '2026-06-30'}
    tid, di, df, nome = _extrair_filtros_temporada(args, {'id': 1}, temporadas)
    assert tid == 2
    assert di == '2026-01-01'
    assert df == '2026-06-30'
    assert nome == 'Temporada 2'

    # Caso 4: 'geral' explicito
    args = {'temporada': 'geral'}
    tid, di, df, nome = _extrair_filtros_temporada(args, {'id': 1}, temporadas)
    assert tid == 'geral'
    assert nome == 'Geral (All-time)'

    # Caso 5: Temporada invalida (string nao numerica) -> cai em geral
    args = {'temporada': 'invalida'}
    tid, di, df, nome = _extrair_filtros_temporada(args, {'id': 1}, temporadas)
    assert tid == 'geral'
    assert nome == 'Geral (All-time)'


def test_dashboard_duelista_renderiza_nome_temporada_atual(client, monkeypatch):
    mock_duelista = {
        'duelista': {'nome': 'Yugi Muto', 'ativo': 1, 'pontos': 30, 'vitorias': 10, 'derrotas': 2, 'empates': 0, 'participacao': 5},
        'resumo': {
            'posicao_ranking': 1,
            'pontos': 30,
            'vitorias': 10,
            'derrotas': 2,
            'empates': 0,
            'win_rate_geral': 83.33,
            'participacao': 5,
            'partidas_total': 12,
            'tops': 4,
            'campeonatos': 2,
            'taxa_conversao_top_titulo': 50.0,
            'qtd_torneios_historico': 5,
        },
        'conquistas': [],
        'historico': [],
    }
    temporadas = [{'id': 1, 'nome': 'Temporada 2026', 'ativa': 1}]

    monkeypatch.setattr(PublicService, 'carregar_dashboard_duelista', lambda self, *args, **kwargs: mock_duelista)
    monkeypatch.setattr(PublicService, 'listar_temporadas', lambda self: temporadas)
    monkeypatch.setattr(PublicService, 'obter_temporada_ativa', lambda self: temporadas[0])

    resp = client.get('/dashboard/duelista/Yugi Muto?temporada=1')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert 'id="duelista-share-card"' in html
    assert 'Temporada 2026 &bull; Duelist Card' in html


def test_handler_404_rota_inexistente(client):
    resp = client.get('/rota_que_definitivamente_nao_existe_12345')

    assert resp.status_code == 404
    html = resp.get_data(as_text=True)
    assert 'Página Não Encontrada - Liga YGO Marabá' in html
    assert 'Carta Não Encontrada!' in html
    assert '404' in html
    assert 'Voltar ao Início' in html
    assert 'Ver Ranking' in html


def test_handler_500_simulando_falha(client, monkeypatch):
    def _mock_falha(*args, **kwargs):
        raise RuntimeError('Falha interna simulada no servidor!')

    monkeypatch.setattr(PublicService, 'obter_resumo_home', _mock_falha)
    client.application.config['PROPAGATE_EXCEPTIONS'] = False

    resp = client.get('/')

    assert resp.status_code == 500
    html = resp.get_data(as_text=True)
    assert 'Erro Interno - Liga YGO Marabá' in html
    assert 'Efeito Inesperado no Duelo!' in html
    assert '500' in html
    assert 'Voltar ao Início' in html
    assert 'Recarregar Página' in html
    # Garante que detalhes internos e stacktrace não são expostos
    assert 'Falha interna simulada' not in html
    assert 'Traceback' not in html


def test_sw_js_endpoint_serves_service_worker(client):
    resp = client.get('/sw.js')

    assert resp.status_code == 200
    assert 'application/javascript' in resp.headers.get('Content-Type', '')
    assert resp.headers.get('Service-Worker-Allowed') == '/'
    content = resp.get_data(as_text=True)
    assert 'ygo-cache-v1' in content
    assert 'self.addEventListener' in content


def test_manifest_json_servido_com_sucesso(client):
    resp = client.get('/static/manifest.json')

    assert resp.status_code == 200
    data = resp.json
    assert data['name'] == 'Liga YGO Marabá - TCG League'
    assert data['short_name'] == 'Liga YGO'
    assert data['start_url'] == '/'
    assert data['display'] == 'standalone'
    assert data['theme_color'] == '#2563eb'
    assert len(data['icons']) >= 3


def test_home_contem_tags_pwa(client):
    resp = client.get('/')

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'rel="manifest"' in html
    assert 'manifest.json' in html
    assert 'name="theme-color" content="#2563eb"' in html
    assert 'apple-mobile-web-app-capable' in html
    assert 'apple-touch-icon' in html


def test_icones_pwa_acessiveis(client):
    for icon_path in ['/static/icons/icon.svg', '/static/icons/icon-192.png', '/static/icons/icon-512.png']:
        resp = client.get(icon_path)
        assert resp.status_code == 200
        assert len(resp.data) > 0



