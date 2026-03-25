import os

from core.models import Torneio


class AdminService:
    def __init__(self, conexao, ordenar_duelistas_para_rank):
        self.conexao = conexao
        self.ordenar_duelistas_para_rank = ordenar_duelistas_para_rank

    def autenticar_admin(self, username, password):
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', '')

        if not admin_password:
            return False, 'ADMIN_PASSWORD nao esta configurada no ambiente de producao.'

        if username == admin_username and password == admin_password:
            return True, ''

        return False, 'Usuario ou senha invalidos.'

    def cadastrar_torneio(self, nome, rodadas_raw, duelistas_raw, data):
        try:
            rodadas = int(rodadas_raw)
            duelistas = int(duelistas_raw)
        except (TypeError, ValueError):
            return False, None, 'Rodadas e duelistas devem ser numeros inteiros validos.'

        if not nome or not data:
            return False, None, 'O nome do torneio e a data nao podem estar vazios.'

        if rodadas <= 0 or duelistas <= 0:
            return False, None, 'Os valores de rodadas e duelistas devem ser positivos.'

        torneio = Torneio(nome, rodadas, duelistas, data)
        torneio_id = self.conexao.cadastrar_torneio(torneio)
        return True, torneio_id, 'Torneio cadastrado com sucesso!'

    def buscar_duelistas(self, status_filtro='todos', nome_busca=''):
        duelistas = self.conexao.carregar_duelistas(incluir_inativos=True)

        if status_filtro == 'ativos':
            duelistas = [d for d in duelistas if d.ativo == 1]
        elif status_filtro == 'inativos':
            duelistas = [d for d in duelistas if d.ativo == 0]

        duelistas_ordenados = self.ordenar_duelistas_para_rank(duelistas)
        duelistas_ordenados = sorted(duelistas_ordenados, key=lambda d: d.ativo, reverse=True)

        duelista_encontrado = None
        posicao_encontrada = None

        if nome_busca:
            for posicao, duelista in enumerate(duelistas_ordenados, start=1):
                if nome_busca.casefold() == duelista.nome.casefold():
                    duelista_encontrado = duelista
                    posicao_encontrada = posicao
                    break

        return {
            'duelistas': duelistas_ordenados,
            'duelista_encontrado': duelista_encontrado,
            'posicao_encontrada': posicao_encontrada,
            'status_filtro': status_filtro,
        }

    def obter_duelista_por_nome(self, nome):
        lista_duelistas = self.conexao.carregar_duelistas()
        for duelista in lista_duelistas:
            if duelista.nome.casefold() == nome.casefold():
                return duelista
        return None

    def atualizar_duelista(self, duelista, novo_nome, vitorias_raw, derrotas_raw, empates_raw):
        try:
            vitorias = int(vitorias_raw)
            derrotas = int(derrotas_raw)
            empates = int(empates_raw)
        except (TypeError, ValueError):
            return False, 'Vitorias, derrotas e empates devem ser numeros inteiros validos.'

        if not novo_nome:
            return False, 'O nome do duelista nao pode estar vazio.'

        if vitorias < 0 or derrotas < 0 or empates < 0:
            return False, 'Os valores de vitorias, derrotas e empates devem ser nao negativos.'

        nome_antigo = duelista.nome
        duelista.nome = novo_nome
        duelista.vitorias = vitorias
        duelista.derrotas = derrotas
        duelista.empates = empates

        self.conexao.atualizar_registro_duelista(
            nome_antigo,
            novo_nome,
            vitorias,
            derrotas,
            empates,
            duelista.pontos,
        )
        return True, 'Dados do duelista atualizados com sucesso!'

    def validar_payload_participacao(self, nome, vitorias_raw, derrotas_raw, empates_raw, topou_torneio, colocacao_top_raw):
        try:
            vitorias = int(vitorias_raw)
            derrotas = int(derrotas_raw)
            empates = int(empates_raw)
        except (TypeError, ValueError):
            return False, None, 'Vitorias, derrotas e empates devem ser numeros inteiros validos.'

        colocacao_top = None
        if topou_torneio:
            if not colocacao_top_raw:
                return False, None, 'Informe a colocacao final no Top Cut.'
            try:
                colocacao_top = int(colocacao_top_raw)
            except ValueError:
                return False, None, 'A colocacao do Top Cut deve ser um numero inteiro.'

        if not nome:
            return False, None, 'O nome do duelista nao pode estar vazio.'

        if vitorias < 0 or derrotas < 0 or empates < 0:
            return False, None, 'Os valores devem ser nao negativos.'

        if topou_torneio and colocacao_top is not None and colocacao_top <= 0:
            return False, None, 'A colocacao do Top Cut deve ser maior que zero.'

        return (
            True,
            {
                'nome': nome,
                'vitorias': vitorias,
                'derrotas': derrotas,
                'empates': empates,
                'topou_torneio': topou_torneio,
                'colocacao_top': colocacao_top,
            },
            '',
        )

    def registrar_participacao(self, torneio_id, payload):
        self.conexao.adicionar_participante_torneio(
            torneio_id,
            payload['nome'],
            payload['vitorias'],
            payload['derrotas'],
            payload['empates'],
            topou_torneio=payload['topou_torneio'],
            colocacao_top=payload['colocacao_top'],
        )
        return f"Participacao de {payload['nome']} registrada com sucesso!"

    def desativar_duelista(self, nome):
        self.conexao.desativar_duelista(nome)
        return (
            f'Duelista {nome} foi inativado! Seu historico permanecera nos torneios, '
            'mas ele ocultado do Ranking atual.'
        )

    def reativar_duelista(self, nome):
        self.conexao.reativar_duelista(nome)
        return f'Duelista {nome} foi reativado e voltou a aparecer no ranking!'

    def excluir_duelista_definitivo(self, nome):
        excluido, detalhe = self.conexao.excluir_duelista_definitivo(nome)

        if excluido:
            return True, f'Duelista {nome} foi excluido definitivamente.'

        if detalhe == 'nao_encontrado':
            return False, 'Duelista nao encontrado.'

        return (
            False,
            f'Nao foi possivel excluir {nome}: existem {detalhe} participacoes no historico de torneios. '
            'Mantenha-o inativo para preservar o historico.',
        )

    def excluir_torneio(self, torneio_id):
        self.conexao.excluir_torneio(torneio_id)
        return 'Torneio excluido com sucesso!'
