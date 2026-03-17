class Duelistas:
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

    def adicionar_pontos(self, vitorias: int, derrotas: int, empates: int):
        self.vitorias += vitorias
        self.derrotas += derrotas
        self.empates += empates
        self.participacao += 1

    def __str__(self):
        return f"Nome: {self.nome}, Vitórias: {self.vitorias}, Derrotas: {self.derrotas}, Empates: {self.empates}, Participação: {self.participacao}, Pontos: {self.pontos}, Ativo: {self.ativo}"

class Torneio:
    def __init__(self, nome: str, rodadas: int, quant_duelistas: int, data: str):
        self.nome = nome
        self.rodadas = rodadas
        self.quant_duelistas = quant_duelistas
        self.data = data
        self.participantes = []

    def adicionar_participantes(self, participante: Duelistas):
        self.participantes.append(participante)

    def __str__(self):
        nomes_participantes = [p.nome for p in self.participantes]
        return f"Nome: {self.nome}, Rodadas: {self.rodadas}, Quant de Duelistas: {self.quant_duelistas}, Data: {self.data}, Participantes: {nomes_participantes}"
                        


