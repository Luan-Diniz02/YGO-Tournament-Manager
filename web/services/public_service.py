class PublicService:
    def __init__(self, conexao, ordenar_duelistas_para_rank):
        self.conexao = conexao
        self.ordenar_duelistas_para_rank = ordenar_duelistas_para_rank

    def health_status(self):
        conexao_bd = None
        cursor = None
        try:
            conexao_bd = self.conexao.conectar_bd()
            cursor = conexao_bd.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            return {'status': 'ok', 'database': 'up'}, 200
        except Exception as e:
            return {'status': 'degraded', 'database': 'down', 'error': str(e)}, 503
        finally:
            if cursor:
                cursor.close()
            if conexao_bd:
                conexao_bd.close()

    def carregar_ranking(self):
        duelistas = self.conexao.carregar_duelistas()
        return self.ordenar_duelistas_para_rank(duelistas)

    def dashboard_default(self):
        return {
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

    def carregar_dashboard(self):
        return self.conexao.obter_estatisticas_dashboard()

    def carregar_dashboard_duelista(self, nome):
        return self.conexao.obter_estatisticas_duelista(nome)

    def listar_torneios(self):
        return self.conexao.listar_torneios()

    def carregar_painel_torneio(self, torneio_id):
        torneio = self.conexao.get_torneio(torneio_id)
        if not torneio:
            return None

        return {
            'torneio': torneio,
            'participantes': self.conexao.listar_participantes_torneio(torneio_id),
            'todos_duelistas': self.conexao.carregar_duelistas(),
        }
