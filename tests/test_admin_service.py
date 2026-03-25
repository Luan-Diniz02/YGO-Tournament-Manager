from types import SimpleNamespace

from web.services.admin_service import AdminService


class DuelistaFake:
    def __init__(self, nome, vitorias=0, derrotas=0, empates=0, participacao=1, ativo=1):
        self.nome = nome
        self.vitorias = vitorias
        self.derrotas = derrotas
        self.empates = empates
        self.participacao = participacao
        self.ativo = ativo

    @property
    def pontos(self):
        return (self.vitorias * 3) + self.empates + self.participacao


class ConexaoFakeAdmin:
    def __init__(self):
        self.torneio_cadastrado = None
        self.duelistas = [
            DuelistaFake('Yugi', 3, 0, 0, 1, 1),
            DuelistaFake('Kaiba', 2, 1, 0, 1, 0),
        ]
        self.atualizacao_args = None
        self.participacao_args = None

    def cadastrar_torneio(self, torneio):
        self.torneio_cadastrado = torneio
        return 42

    def carregar_duelistas(self, incluir_inativos=False):
        if incluir_inativos:
            return self.duelistas
        return [d for d in self.duelistas if d.ativo == 1]

    def atualizar_registro_duelista(self, *args):
        self.atualizacao_args = args

    def adicionar_participante_torneio(self, *args, **kwargs):
        self.participacao_args = (args, kwargs)

    def desativar_duelista(self, nome):
        return nome

    def reativar_duelista(self, nome):
        return nome

    def excluir_duelista_definitivo(self, nome):
        if nome == 'inexistente':
            return False, 'nao_encontrado'
        if nome == 'com_historico':
            return False, 3
        return True, 0

    def excluir_torneio(self, torneio_id):
        return torneio_id


def ordenar_duelistas(duelistas):
    return sorted(duelistas, key=lambda d: (-d.pontos, d.derrotas, d.nome.casefold()))


def test_autenticar_admin_sucesso(monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'segredo')
    service = AdminService(ConexaoFakeAdmin(), ordenar_duelistas)

    ok, mensagem = service.autenticar_admin('admin', 'segredo')

    assert ok is True
    assert mensagem == ''


def test_autenticar_admin_sem_senha_configurada(monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD', '')
    service = AdminService(ConexaoFakeAdmin(), ordenar_duelistas)

    ok, mensagem = service.autenticar_admin('admin', 'qualquer')

    assert ok is False
    assert 'ADMIN_PASSWORD' in mensagem


def test_cadastrar_torneio_com_dados_validos():
    conexao = ConexaoFakeAdmin()
    service = AdminService(conexao, ordenar_duelistas)

    ok, torneio_id, mensagem = service.cadastrar_torneio('Etapa 1', '4', '16', '2026-03-25')

    assert ok is True
    assert torneio_id == 42
    assert 'sucesso' in mensagem.lower()
    assert conexao.torneio_cadastrado.nome == 'Etapa 1'


def test_cadastrar_torneio_com_valor_invalido():
    service = AdminService(ConexaoFakeAdmin(), ordenar_duelistas)

    ok, torneio_id, mensagem = service.cadastrar_torneio('Etapa', 'x', '16', '2026-03-25')

    assert ok is False
    assert torneio_id is None
    assert 'inteiros' in mensagem


def test_buscar_duelistas_filtra_ativos_e_localiza_nome():
    service = AdminService(ConexaoFakeAdmin(), ordenar_duelistas)

    resultado = service.buscar_duelistas(status_filtro='ativos', nome_busca='yugi')

    assert len(resultado['duelistas']) == 1
    assert resultado['duelista_encontrado'] is not None
    assert resultado['duelista_encontrado'].nome == 'Yugi'
    assert resultado['posicao_encontrada'] == 1


def test_atualizar_duelista_valido_persiste():
    conexao = ConexaoFakeAdmin()
    service = AdminService(conexao, ordenar_duelistas)
    duelista = conexao.duelistas[0]

    ok, mensagem = service.atualizar_duelista(duelista, 'Yami Yugi', '5', '1', '0')

    assert ok is True
    assert 'sucesso' in mensagem.lower()
    assert duelista.nome == 'Yami Yugi'
    assert conexao.atualizacao_args is not None


def test_validar_payload_participacao_com_top_cut_invalido():
    service = AdminService(ConexaoFakeAdmin(), ordenar_duelistas)

    ok, payload, mensagem = service.validar_payload_participacao('Yugi', '3', '1', '0', True, '')

    assert ok is False
    assert payload is None
    assert 'Top Cut' in mensagem


def test_excluir_duelista_definitivo_retorna_mensagem_historico():
    service = AdminService(ConexaoFakeAdmin(), ordenar_duelistas)

    ok, mensagem = service.excluir_duelista_definitivo('com_historico')

    assert ok is False
    assert 'participacoes' in mensagem
