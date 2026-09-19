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

    def carregar_dashboard(self, temporada_id=None, data_inicio=None, data_fim=None):
        return self.conexao.obter_estatisticas_dashboard(
            temporada_id=temporada_id, data_inicio=data_inicio, data_fim=data_fim
        )

    def carregar_dashboard_duelista(self, nome, temporada_id=None, data_inicio=None, data_fim=None):
        return self.conexao.obter_estatisticas_duelista(
            nome, temporada_id=temporada_id, data_inicio=data_inicio, data_fim=data_fim
        )

    def listar_temporadas(self):
        return self.conexao.listar_temporadas()
        
    def obter_temporada_ativa(self):
        return self.conexao.obter_temporada_ativa()

    def listar_torneios(self, temporada_id=None):
        return self.conexao.listar_torneios(temporada_id=temporada_id)

    def carregar_painel_torneio(self, torneio_id):
        torneio = self.conexao.get_torneio(torneio_id)
        if not torneio:
            return None

        return {
            'torneio': torneio,
            'participantes': self.conexao.listar_participantes_torneio(torneio_id),
            'todos_duelistas': self.conexao.carregar_duelistas(),
        }

    def obter_resumo_home(self):
        temp_ativa = self.obter_temporada_ativa()
        temporada_id = temp_ativa['id'] if temp_ativa else None

        try:
            dashboard = self.carregar_dashboard(temporada_id=temporada_id)
        except Exception:
            dashboard = self.dashboard_default()

        resumo = dashboard.get('resumo', {})
        duelistas = dashboard.get('duelistas', [])
        lider = duelistas[0] if duelistas else None

        torneios = self.listar_torneios(temporada_id=temporada_id) if temporada_id else self.listar_torneios()
        total_torneios = len(torneios) if torneios else 0

        ultimo_torneio = None
        if torneios:
            t = torneios[0]
            campeao = None
            try:
                participantes = self.conexao.listar_participantes_torneio(t['id'])
                if participantes:
                    campeao = participantes[0]
            except Exception:
                campeao = None

            ultimo_torneio = {
                'id': t['id'],
                'nome': t['nome'],
                'data': t.get('data'),
                'qtd_participantes': t.get('qtd_participantes', 0),
                'campeao_nome': campeao['nome'] if campeao else None,
                'campeao_vitorias': campeao['vitorias'] if campeao else None,
                'campeao_derrotas': campeao['derrotas'] if campeao else None,
            }

        return {
            'temporada_ativa': temp_ativa,
            'metricas': {
                'total_torneios': total_torneios,
                'total_duelistas': resumo.get('total_duelistas', 0),
                'total_partidas': resumo.get('total_partidas', 0),
            },
            'lider': lider,
            'ultimo_torneio': ultimo_torneio,
        }
