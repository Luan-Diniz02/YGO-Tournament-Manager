from web.services.public_service import PublicService


class CursorFake:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def execute(self, _sql):
        if self.should_fail:
            raise RuntimeError('db down')

    def fetchone(self):
        return (1,)

    def close(self):
        return None


class ConexaoBdFake:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def cursor(self):
        return CursorFake(should_fail=self.should_fail)

    def close(self):
        return None


class ConexaoFakePublic:
    def __init__(self, db_fail=False):
        self.db_fail = db_fail

    def conectar_bd(self):
        return ConexaoBdFake(should_fail=self.db_fail)

    def obter_estatisticas_dashboard(self):
        return {'resumo': {'total_duelistas': 2}, 'lideres': {}, 'duelistas': []}

    def obter_estatisticas_duelista(self, nome):
        if nome == 'inexistente':
            return None
        return {'duelista': {'nome': nome}}

    def listar_torneios(self):
        return [{'id': 1, 'nome': 'Etapa 1'}]

    def get_torneio(self, torneio_id):
        if torneio_id == 99:
            return None
        return {'id': torneio_id, 'nome': 'Etapa'}

    def listar_participantes_torneio(self, _torneio_id):
        return [{'nome': 'Yugi'}]

    def carregar_duelistas(self):
        return [
            type('D', (), {'nome': 'Yugi', 'pontos': 10, 'derrotas': 1})(),
            type('D', (), {'nome': 'Kaiba', 'pontos': 7, 'derrotas': 2})(),
        ]


def ordenar_duelistas(duelistas):
    return list(duelistas)


def test_health_status_ok():
    service = PublicService(ConexaoFakePublic(db_fail=False), ordenar_duelistas)

    payload, status = service.health_status()

    assert status == 200
    assert payload['status'] == 'ok'


def test_health_status_degraded():
    service = PublicService(ConexaoFakePublic(db_fail=True), ordenar_duelistas)

    payload, status = service.health_status()

    assert status == 503
    assert payload['status'] == 'degraded'


def test_dashboard_default_tem_estrutura_base():
    service = PublicService(ConexaoFakePublic(), ordenar_duelistas)

    dados = service.dashboard_default()

    assert 'resumo' in dados
    assert 'lideres' in dados
    assert 'duelistas' in dados


def test_carregar_painel_torneio_quando_existe():
    service = PublicService(ConexaoFakePublic(), ordenar_duelistas)

    dados = service.carregar_painel_torneio(1)

    assert dados is not None
    assert dados['torneio']['id'] == 1
    assert len(dados['participantes']) == 1


def test_carregar_painel_torneio_quando_nao_existe():
    service = PublicService(ConexaoFakePublic(), ordenar_duelistas)

    dados = service.carregar_painel_torneio(99)

    assert dados is None
