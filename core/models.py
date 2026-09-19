class Duelistas:
    """
    Representa a entidade de um duelista e seu histórico/snapshot agregado de pontuação.

    Modelagem de Pontuações e Regra do Yu-Gi-Oh! Moderno:
    - No jogo oficial competitivo (Yu-Gi-Oh! TCG / OTS Tournament Rules), partidas não
      terminam em empate; caso o tempo limite expire em condições de igualdade ou ocorra
      Double Game Loss na rodada decisiva, aplica-se Double Loss (derrota mútua para ambos
      os duelistas), concedendo 0 pontos a ambos.
    - O atributo `empates` (default = 0) é mantido para garantir compatibilidade retroativa
      com o schema do banco legado e eventuais formatos customizados/históricos.
    - Fórmula oficial de pontuação agregada:
          pontos = (vitorias * 3) + empates + participacao
      onde:
          * Cada vitória concede 3 pontos;
          * Cada empate (caso existente em formato legado/customizado) concede 1 ponto;
          * Cada participação em torneio concede 1 ponto de presença/incentivo.
    """

    def __init__(self, nome: str, vitorias: int = 0, derrotas: int = 0, empates: int = 0, participacao: int = 1, ativo: int = 1):
        self.nome = nome
        self.vitorias = int(vitorias)
        self.derrotas = int(derrotas)
        self.empates = int(empates)
        self.participacao = participacao
        self.ativo = int(ativo)

    @property
    def pontos(self) -> int:
        return (self.vitorias * 3) + self.empates + self.participacao

    def adicionar_pontos(self, vitorias: int, derrotas: int, empates: int = 0):
        self.vitorias += vitorias
        self.derrotas += derrotas
        self.empates += empates
        self.participacao += 1

    def __str__(self):
        return f"Nome: {self.nome}, Vitórias: {self.vitorias}, Derrotas: {self.derrotas}, Empates: {self.empates}, Participação: {self.participacao}, Pontos: {self.pontos}, Ativo: {self.ativo}"

class Torneio:
    """
    Representa um evento ou torneio de Yu-Gi-Oh!.

    Atributos:
        nome (str): Nome descritivo do torneio.
        rodadas (int): Quantidade de rodadas suíças ou eliminatórias disputadas no evento.
        quant_duelistas (int): Quantidade total de jogadores inscritos/planejados.
        data (str): Data de realização do evento (formato ISO/YYYY-MM-DD).
        temporada_id (int, opcional): Identificador da temporada associada ao torneio.
        participantes (list): Lista de instâncias de Duelistas vinculadas ao evento.
    """

    def __init__(self, nome: str, rodadas: int, quant_duelistas: int, data: str, temporada_id: int = None):
        self.nome = nome
        self.rodadas = rodadas
        self.quant_duelistas = quant_duelistas
        self.data = data
        self.temporada_id = temporada_id
        self.participantes = []

    def adicionar_participantes(self, participante: Duelistas):
        self.participantes.append(participante)

    def __str__(self):
        nomes_participantes = [p.nome for p in self.participantes]
        return f"Nome: {self.nome}, Rodadas: {self.rodadas}, Quant de Duelistas: {self.quant_duelistas}, Data: {self.data}, Participantes: {nomes_participantes}"
                        


