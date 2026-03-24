import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode
from core.models import Duelistas

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Conexao:
    @staticmethod
    def _parse_bool(value, default=False):
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def __init__(self):
        # Utiliza as variáveis de ambiente, com valores padrão caso não encontre
        self.host = os.getenv("DB_HOST", "127.0.0.1")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "root")
        self.database = os.getenv("DB_NAME", "torneio")
        self.ssl_disabled = self._parse_bool(os.getenv("DB_SSL_DISABLED"), default=False)
        self.ssl_ca = os.getenv("DB_SSL_CA", "").strip()
        self.ssl_verify_cert = self._parse_bool(os.getenv("DB_SSL_VERIFY_CERT"), default=False)
        self.ssl_verify_identity = self._parse_bool(os.getenv("DB_SSL_VERIFY_IDENTITY"), default=False)

    def _coluna_existe(self, cursor, tabela, coluna):
        cursor.execute(
            """
            SELECT 1
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
            LIMIT 1
            """,
            (self.database, tabela, coluna),
        )
        return cursor.fetchone() is not None

    def conectar_bd(self):
        conn_kwargs = dict(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )

        # Permite conexão com provedores MySQL gerenciados que exigem TLS.
        if self.ssl_disabled:
            conn_kwargs["ssl_disabled"] = True
        else:
            if self.ssl_ca:
                conn_kwargs["ssl_ca"] = self.ssl_ca
            if "DB_SSL_VERIFY_CERT" in os.environ:
                conn_kwargs["ssl_verify_cert"] = self.ssl_verify_cert
            if "DB_SSL_VERIFY_IDENTITY" in os.environ:
                conn_kwargs["ssl_verify_identity"] = self.ssl_verify_identity

        return mysql.connector.connect(**conn_kwargs)

    def garantir_estrutura_bd(self):
        """Cria as tabelas necessárias caso ainda não existam (idempotente)."""
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS duelistas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(120) NOT NULL UNIQUE,
                    vitorias INT NOT NULL DEFAULT 0,
                    derrotas INT NOT NULL DEFAULT 0,
                    empates INT NOT NULL DEFAULT 0,
                    participacao INT NOT NULL DEFAULT 0,
                    pontos INT NOT NULL DEFAULT 0,
                    ativo TINYINT(1) NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_duelistas_ativo (ativo),
                    INDEX idx_duelistas_pontos (pontos)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS torneios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(120) NOT NULL,
                    rodadas INT NOT NULL,
                    quant_duelistas INT NOT NULL,
                    data DATE NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_torneios_data (data)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS torneio_participantes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    torneio_id INT NOT NULL,
                    duelista_id INT NOT NULL,
                    vitorias INT NOT NULL DEFAULT 0,
                    derrotas INT NOT NULL DEFAULT 0,
                    empates INT NOT NULL DEFAULT 0,
                    pontos_obtidos INT NOT NULL DEFAULT 0,
                    topou_torneio TINYINT(1) NOT NULL DEFAULT 0,
                    colocacao_top INT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_tp_torneio FOREIGN KEY (torneio_id)
                        REFERENCES torneios(id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_tp_duelista FOREIGN KEY (duelista_id)
                        REFERENCES duelistas(id)
                        ON DELETE RESTRICT,
                    UNIQUE KEY uk_tp_torneio_duelista (torneio_id, duelista_id),
                    INDEX idx_tp_torneio (torneio_id),
                    INDEX idx_tp_duelista (duelista_id)
                )
            """)

            # Migração leve para bases antigas que não possuem os novos campos.
            if not self._coluna_existe(cursor, 'torneio_participantes', 'topou_torneio'):
                cursor.execute(
                    "ALTER TABLE torneio_participantes ADD COLUMN topou_torneio TINYINT(1) NOT NULL DEFAULT 0"
                )
            if not self._coluna_existe(cursor, 'torneio_participantes', 'colocacao_top'):
                cursor.execute(
                    "ALTER TABLE torneio_participantes ADD COLUMN colocacao_top INT NULL"
                )

            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()

    def encontrar_duelista(self, nome):
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor()
            sql = "SELECT * FROM duelistas WHERE nome = %s"
            cursor.execute(sql, (nome,))
            duelista = cursor.fetchone()
            return duelista
        finally:
            conexao.close()

    def listar_duelistas(self, incluir_inativos=False):
        def executar_consulta():
            conexao = self.conectar_bd()
            try:
                cursor = conexao.cursor(dictionary=True)
                if incluir_inativos:
                    sql = "SELECT * FROM duelistas"
                else:
                    sql = "SELECT * FROM duelistas WHERE ativo = 1"
                cursor.execute(sql)
                return cursor.fetchall()
            finally:
                conexao.close()

        try:
            return executar_consulta()
        except mysql.connector.Error as e:
            # Primeira execução em produção pode chegar sem tabelas criadas.
            if e.errno == errorcode.ER_NO_SUCH_TABLE:
                self.garantir_estrutura_bd()
                return executar_consulta()
            raise

    def adicionar_pontos(self, nome, vitorias, derrotas, empates):
        conexao = self.conectar_bd()
        is_new = False
        try:
            cursor = conexao.cursor()

            # Verifica se o duelist já existe na tabela
            sql_select = "SELECT * FROM duelistas WHERE nome = %s"
            cursor.execute(sql_select, (nome,))
            duelistas = cursor.fetchall()

            if duelistas:  # Se o duelist já existir na tabela
                # Atualiza os valores de vitórias, derrotas e empates para o duelista, e volta a ficar ativo se não estiver
                sql_update = ("UPDATE duelistas SET vitorias = vitorias + %s, derrotas = derrotas + %s, empates = empates + %s,"
                              "participacao = participacao+1, pontos= (vitorias*3)+empates+participacao, ativo = 1 WHERE nome = %s")
                val = (vitorias, derrotas, empates, nome)
                cursor.execute(sql_update, val)
                is_new = False
            else:  # Se o duelist não existir na tabela, insere um novo registro
                sql_insert = "INSERT INTO duelistas (nome, vitorias, derrotas, empates, participacao, pontos, ativo) VALUES (%s, %s, %s, %s, %s, %s, 1)"
                val = (nome, vitorias, derrotas, empates, 1, (vitorias*3)+empates+1)
                cursor.execute(sql_insert, val)
                is_new = True

            conexao.commit()
            return is_new
        except Exception as e:
            conexao.rollback()
            print(f"Erro ao adicionar pontos: {e}")
            raise e
        finally:
            conexao.close()

    def carregar_duelistas(self, incluir_inativos=False):

        dados = self.listar_duelistas(incluir_inativos=incluir_inativos)
        
        lista_duelistas = []
        for data in dados:
            duelista = Duelistas(
                nome=data['nome'],
                vitorias=int(data['vitorias']),
                derrotas=int(data['derrotas']),
                empates=int(data['empates']),
                participacao=int(data['participacao']),
                ativo=int(data.get('ativo', 1)),
            )
            lista_duelistas.append(duelista)
        
        return lista_duelistas
    
    def atualizar_registro_duelista(self, nome_antigo, novo_nome, vitorias, derrotas, empates, pontos):
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor()
            sql = """
                UPDATE duelistas 
                SET nome = %s, vitorias = %s, derrotas = %s, empates = %s, pontos = %s
                WHERE nome = %s
            """
            cursor.execute(sql, (novo_nome, vitorias, derrotas, empates, pontos, nome_antigo))
            conexao.commit()
        except Exception as e:
            print(f"Erro ao atualizar duelista: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conexao' in locals() and conexao.is_connected():
                conexao.close()

    def atualizar_bd(self, lista_duelistas):
        if not lista_duelistas:
            return

        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor()

            # Prepara os dados para inserção em lote
            valores = [
                (d.nome, d.vitorias, d.derrotas, d.empates, d.participacao, d.pontos)
                for d in lista_duelistas
            ]

            # O MySQL suporta o comando 'ON DUPLICATE KEY UPDATE'. Se o nome existir (presumindo que seja UNIQUE PRIMARY KEY),
            # ele apenas atualiza; se não existir, ele insere o novo. Isso resolve dezenas de instâncias com apenas 1 query.
            sql = """
                INSERT INTO duelistas (nome, vitorias, derrotas, empates, participacao, pontos)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    vitorias = VALUES(vitorias),
                    derrotas = VALUES(derrotas),
                    empates = VALUES(empates),
                    participacao = VALUES(participacao),
                    pontos = VALUES(pontos)
            """
            
            cursor.executemany(sql, valores)
            conexao.commit()
            
        except Exception as e:
            conexao.rollback()
            print(f"Erro ao atualizar BD: {e}")
            raise e
        finally:
            conexao.close()

    def listar_torneios(self):
        """
        Retorna a lista de todos os torneios cadastrados no banco de dados.
        """
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor(dictionary=True)
            sql = """
                SELECT t.*, COUNT(tp.duelista_id) as qtd_participantes 
                FROM torneios t 
                LEFT JOIN torneio_participantes tp ON t.id = tp.torneio_id 
                GROUP BY t.id 
                ORDER BY t.data DESC, t.id DESC
            """
            cursor.execute(sql)
            torneios = cursor.fetchall()
            return torneios
        finally:
            conexao.close()

    def cadastrar_torneio(self, torneio):
        """
        Cadastra um novo torneio no banco de dados
        """
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor()
            
            sql = """INSERT INTO torneios (nome, rodadas, quant_duelistas, data) 
                     VALUES (%s, %s, %s, %s)"""
            val = (torneio.nome, torneio.rodadas, torneio.quant_duelistas, torneio.data)
            
            cursor.execute(sql, val)
            conexao.commit()
            
            print(f"Torneio '{torneio.nome}' cadastrado com sucesso!")
            return cursor.lastrowid
        except Exception as e:
            conexao.rollback()
            print(f"Erro ao cadastrar torneio: {e}")
            raise e
        finally:
            conexao.close()

    def get_torneio(self, torneio_id):
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM torneios WHERE id = %s", (torneio_id,))
            return cursor.fetchone()
        finally:
            conexao.close()
            
    def desativar_duelista(self, nome):
        """Inativa um duelista para não sumir do histórico em torneios passados"""
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor()
            cursor.execute("UPDATE duelistas SET ativo = 0 WHERE nome = %s", (nome,))
            conexao.commit()
        except Exception as e:
            conexao.rollback()
            raise e
        finally:
            conexao.close()

    def reativar_duelista(self, nome):
        """Reativa um duelista previamente inativado"""
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor()
            cursor.execute("UPDATE duelistas SET ativo = 1 WHERE nome = %s", (nome,))
            conexao.commit()
        except Exception as e:
            conexao.rollback()
            raise e
        finally:
            conexao.close()

    def excluir_duelista_definitivo(self, nome):
        """Exclui duelista de forma definitiva apenas se não houver histórico em torneios."""
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor(dictionary=True)

            cursor.execute("SELECT id FROM duelistas WHERE nome = %s", (nome,))
            duelista = cursor.fetchone()

            if not duelista:
                return False, "nao_encontrado"

            cursor.execute(
                "SELECT COUNT(*) AS total FROM torneio_participantes WHERE duelista_id = %s",
                (duelista['id'],)
            )
            total_participacoes = cursor.fetchone()['total']

            if total_participacoes > 0:
                return False, total_participacoes

            cursor.execute("DELETE FROM duelistas WHERE id = %s", (duelista['id'],))
            conexao.commit()
            return True, 0
        except Exception as e:
            conexao.rollback()
            raise e
        finally:
            conexao.close()

    def excluir_torneio(self, torneio_id):
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM torneios WHERE id = %s", (torneio_id,))
            conexao.commit()
        except Exception as e:
            conexao.rollback()
            raise e
        finally:
            conexao.close()

    def listar_participantes_torneio(self, torneio_id):
        def executar_consulta():
            conexao = self.conectar_bd()
            try:
                cursor = conexao.cursor(dictionary=True)
                sql = """
                    SELECT tp.id as tp_id, d.nome, d.ativo, tp.vitorias, tp.derrotas, tp.empates, tp.pontos_obtidos,
                           tp.topou_torneio, tp.colocacao_top
                    FROM torneio_participantes tp
                    JOIN duelistas d ON tp.duelista_id = d.id
                    WHERE tp.torneio_id = %s
                    ORDER BY
                        CASE WHEN tp.topou_torneio = 1 AND tp.colocacao_top IS NOT NULL THEN 0 ELSE 1 END,
                        CASE WHEN tp.topou_torneio = 1 AND tp.colocacao_top IS NOT NULL THEN tp.colocacao_top ELSE 9999 END,
                        tp.pontos_obtidos DESC,
                        tp.vitorias DESC,
                        tp.derrotas ASC,
                        d.nome ASC
                """
                cursor.execute(sql, (torneio_id,))
                return cursor.fetchall()
            finally:
                conexao.close()

        try:
            return executar_consulta()
        except mysql.connector.Error as e:
            if e.errno in (errorcode.ER_NO_SUCH_TABLE, errorcode.ER_BAD_FIELD_ERROR):
                self.garantir_estrutura_bd()
                return executar_consulta()
            raise
            
    def adicionar_participante_torneio(self, torneio_id, nome, vitorias, derrotas, empates, topou_torneio=False, colocacao_top=None):
        def executar_operacao():
            conexao = self.conectar_bd()
            try:
                cursor = conexao.cursor(dictionary=True)

                # Garante que o duelista existe na base global
                cursor.execute("SELECT * FROM duelistas WHERE nome = %s", (nome,))
                duelista = cursor.fetchone()

                if not duelista:
                    # Insere caso não exista, com 0 em tudo, para que o bloco abaixo some os valores corretos
                    cursor.execute(
                        "INSERT INTO duelistas (nome, vitorias, derrotas, empates, participacao, pontos, ativo) VALUES (%s, 0, 0, 0, 0, 0, 1)",
                        (nome,)
                    )
                    conexao.commit()
                    cursor.execute("SELECT * FROM duelistas WHERE nome = %s", (nome,))
                    duelista = cursor.fetchone()

                    # Nao tem histórico nesse torneio pq acabou de ser criado
                    hist_torneio = None
                else:
                    # Verifica se o jogador já estava nesse torneio
                    cursor.execute("SELECT * FROM torneio_participantes WHERE torneio_id = %s AND duelista_id = %s", (torneio_id, duelista['id']))
                    hist_torneio = cursor.fetchone()

                pontos_torneio_novos = (vitorias * 3) + empates + 1

                if hist_torneio:
                    # O cara já estava nesse torneio, então queremos SUBSTITUIR/EDITAR o placar dele.
                    # Para não inflar os pontos globais, calculamos a diferença:
                    diff_v = vitorias - hist_torneio['vitorias']
                    diff_d = derrotas - hist_torneio['derrotas']
                    diff_e = empates - hist_torneio['empates']
                    diff_p = (diff_v * 3) + diff_e # A participacao nao muda
                    # Participação global não muda, porque ele já participava desse torneio.

                    # 1. Update no torneio (substituindo pontos e placar)
                    cursor.execute("""
                        UPDATE torneio_participantes
                        SET vitorias = %s,
                            derrotas = %s,
                            empates = %s,
                            pontos_obtidos = %s,
                            topou_torneio = %s,
                            colocacao_top = %s
                        WHERE id = %s
                    """, (vitorias, derrotas, empates, pontos_torneio_novos, int(bool(topou_torneio)), colocacao_top, hist_torneio['id']))

                    # 2. Update global do duelista com as diferenças (recálculo dos pontos totais)
                    # reativando o duelista caso estivesse inativo
                    cursor.execute("""
                        UPDATE duelistas
                        SET vitorias = vitorias + %s,
                            derrotas = derrotas + %s,
                            empates = empates + %s,
                            pontos = pontos + %s,
                            ativo = 1
                        WHERE id = %s
                    """, (diff_v, diff_d, diff_e, diff_p, duelista['id']))
                else:
                    # O cara já existia no BD (ou acabou de ser criado vazio) mas é NOVO nesse torneio
                    # 1. Insert no torneio
                    cursor.execute("""
                        INSERT INTO torneio_participantes (
                            torneio_id, duelista_id, vitorias, derrotas, empates, pontos_obtidos, topou_torneio, colocacao_top
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (torneio_id, duelista['id'], vitorias, derrotas, empates, pontos_torneio_novos, int(bool(topou_torneio)), colocacao_top))

                    # 2. Update global do duelista adicionando os novos stats e +1 participacao
                    cursor.execute("""
                        UPDATE duelistas
                        SET vitorias = vitorias + %s,
                            derrotas = derrotas + %s,
                            empates = empates + %s,
                            participacao = participacao + 1,
                            pontos = pontos + %s,
                            ativo = 1
                        WHERE id = %s
                    """, (vitorias, derrotas, empates, pontos_torneio_novos, duelista['id']))

                conexao.commit()
            finally:
                conexao.close()

        try:
            executar_operacao()
        except mysql.connector.Error as e:
            if e.errno in (errorcode.ER_NO_SUCH_TABLE, errorcode.ER_BAD_FIELD_ERROR):
                self.garantir_estrutura_bd()
                executar_operacao()
                return
            raise

    def obter_estatisticas_dashboard(self, incluir_inativos=False):
        def percentual(numerador, denominador):
            if not denominador:
                return 0.0
            return round((numerador / denominador) * 100, 2)

        def executar_consulta():
            conexao = self.conectar_bd()
            try:
                cursor = conexao.cursor(dictionary=True)

                filtro_status = "" if incluir_inativos else "WHERE d.ativo = 1"

                resumo_sql = f"""
                    SELECT
                        COUNT(*) AS total_duelistas,
                        COALESCE(SUM(d.vitorias), 0) AS total_vitorias,
                        COALESCE(SUM(d.derrotas), 0) AS total_derrotas,
                        COALESCE(SUM(d.empates), 0) AS total_empates,
                        COALESCE(SUM(tp.tops), 0) AS total_tops,
                        COALESCE(SUM(tp.campeonatos), 0) AS total_campeonatos
                    FROM duelistas d
                    LEFT JOIN (
                        SELECT
                            duelista_id,
                            SUM(CASE WHEN topou_torneio = 1 THEN 1 ELSE 0 END) AS tops,
                            SUM(CASE WHEN colocacao_top = 1 THEN 1 ELSE 0 END) AS campeonatos
                        FROM torneio_participantes
                        GROUP BY duelista_id
                    ) tp ON tp.duelista_id = d.id
                    {filtro_status}
                """
                cursor.execute(resumo_sql)
                resumo = cursor.fetchone() or {}

                duelistas_sql = f"""
                    SELECT
                        d.id,
                        d.nome,
                        d.vitorias,
                        d.derrotas,
                        d.empates,
                        d.participacao,
                        d.pontos,
                        d.ativo,
                        COALESCE(tp.tops, 0) AS tops,
                        COALESCE(tp.campeonatos, 0) AS campeonatos
                    FROM duelistas d
                    LEFT JOIN (
                        SELECT
                            duelista_id,
                            SUM(CASE WHEN topou_torneio = 1 THEN 1 ELSE 0 END) AS tops,
                            SUM(CASE WHEN colocacao_top = 1 THEN 1 ELSE 0 END) AS campeonatos
                        FROM torneio_participantes
                        GROUP BY duelista_id
                    ) tp ON tp.duelista_id = d.id
                    {filtro_status}
                    ORDER BY campeonatos DESC, tops DESC, d.pontos DESC, d.vitorias DESC, d.nome ASC
                """
                cursor.execute(duelistas_sql)
                duelistas = cursor.fetchall()

                for duelista in duelistas:
                    partidas = int(duelista['vitorias']) + int(duelista['derrotas']) + int(duelista['empates'])
                    duelista['partidas'] = partidas
                    duelista['win_rate'] = percentual(int(duelista['vitorias']), partidas)
                    duelista['taxa_conversao_top_titulo'] = percentual(int(duelista['campeonatos']), int(duelista['tops']))

                total_vitorias = int(resumo.get('total_vitorias', 0) or 0)
                total_derrotas = int(resumo.get('total_derrotas', 0) or 0)
                total_empates = int(resumo.get('total_empates', 0) or 0)
                total_tops = int(resumo.get('total_tops', 0) or 0)
                total_campeonatos = int(resumo.get('total_campeonatos', 0) or 0)
                total_partidas = total_vitorias + total_derrotas + total_empates

                resumo_formatado = {
                    'total_duelistas': int(resumo.get('total_duelistas', 0) or 0),
                    'total_partidas': total_partidas,
                    'total_vitorias': total_vitorias,
                    'total_derrotas': total_derrotas,
                    'total_empates': total_empates,
                    'total_tops': total_tops,
                    'total_campeonatos': total_campeonatos,
                    'win_rate_geral': percentual(total_vitorias, total_partidas),
                    'taxa_conversao_top_titulo_geral': percentual(total_campeonatos, total_tops),
                }

                lider_maior_win_rate = None
                duelistas_com_partidas = [d for d in duelistas if d['partidas'] > 0]
                if duelistas_com_partidas:
                    lider_maior_win_rate = max(
                        duelistas_com_partidas,
                        key=lambda d: (d['win_rate'], d['partidas'], d['vitorias'])
                    )

                lider_mais_tops = max(duelistas, key=lambda d: (d['tops'], d['campeonatos'], d['pontos']), default=None)
                lider_mais_campeonatos = max(duelistas, key=lambda d: (d['campeonatos'], d['tops'], d['pontos']), default=None)

                return {
                    'resumo': resumo_formatado,
                    'lideres': {
                        'maior_win_rate': lider_maior_win_rate,
                        'mais_tops': lider_mais_tops,
                        'mais_campeonatos': lider_mais_campeonatos,
                    },
                    'duelistas': duelistas,
                }
            finally:
                conexao.close()

        try:
            return executar_consulta()
        except mysql.connector.Error as e:
            if e.errno in (errorcode.ER_NO_SUCH_TABLE, errorcode.ER_BAD_FIELD_ERROR):
                self.garantir_estrutura_bd()
                return executar_consulta()
            raise

    def obter_estatisticas_duelista(self, nome_duelista):
        def percentual(numerador, denominador):
            if not denominador:
                return 0.0
            return round((numerador / denominador) * 100, 2)

        def executar_consulta():
            conexao = self.conectar_bd()
            try:
                cursor = conexao.cursor(dictionary=True)

                cursor.execute(
                    """
                    SELECT
                        d.id,
                        d.nome,
                        d.vitorias,
                        d.derrotas,
                        d.empates,
                        d.participacao,
                        d.pontos,
                        d.ativo,
                        COALESCE(tp.tops, 0) AS tops,
                        COALESCE(tp.campeonatos, 0) AS campeonatos
                    FROM duelistas d
                    LEFT JOIN (
                        SELECT
                            duelista_id,
                            SUM(CASE WHEN topou_torneio = 1 THEN 1 ELSE 0 END) AS tops,
                            SUM(CASE WHEN colocacao_top = 1 THEN 1 ELSE 0 END) AS campeonatos
                        FROM torneio_participantes
                        GROUP BY duelista_id
                    ) tp ON tp.duelista_id = d.id
                    WHERE LOWER(d.nome) = LOWER(%s)
                    LIMIT 1
                    """,
                    (nome_duelista,),
                )
                duelista = cursor.fetchone()
                if not duelista:
                    return None

                cursor.execute(
                    """
                    SELECT
                        t.id AS torneio_id,
                        t.nome AS torneio_nome,
                        t.data AS torneio_data,
                        tp.vitorias,
                        tp.derrotas,
                        tp.empates,
                        tp.pontos_obtidos,
                        tp.topou_torneio,
                        tp.colocacao_top
                    FROM torneio_participantes tp
                    JOIN torneios t ON t.id = tp.torneio_id
                    WHERE tp.duelista_id = %s
                    ORDER BY t.data DESC, t.id DESC
                    """,
                    (duelista['id'],),
                )
                historico = cursor.fetchall()

                for evento in historico:
                    partidas_evento = int(evento['vitorias']) + int(evento['derrotas']) + int(evento['empates'])
                    evento['partidas'] = partidas_evento
                    evento['win_rate_evento'] = percentual(int(evento['vitorias']), partidas_evento)

                    # Calcula a posição final do duelista na etapa, mesmo sem Top Cut.
                    posicao_geral = None
                    participantes_torneio = self.listar_participantes_torneio(evento['torneio_id'])
                    for idx, participante in enumerate(participantes_torneio, start=1):
                        if participante['nome'].casefold() == duelista['nome'].casefold():
                            posicao_geral = idx
                            break
                    evento['posicao_geral'] = posicao_geral

                partidas_total = int(duelista['vitorias']) + int(duelista['derrotas']) + int(duelista['empates'])

                resumo = {
                    'partidas_total': partidas_total,
                    'win_rate_geral': percentual(int(duelista['vitorias']), partidas_total),
                    'tops': int(duelista['tops']),
                    'campeonatos': int(duelista['campeonatos']),
                    'taxa_conversao_top_titulo': percentual(int(duelista['campeonatos']), int(duelista['tops'])),
                    'qtd_torneios_historico': len(historico),
                }

                return {
                    'duelista': duelista,
                    'resumo': resumo,
                    'historico': historico,
                }
            finally:
                conexao.close()

        try:
            return executar_consulta()
        except mysql.connector.Error as e:
            if e.errno in (errorcode.ER_NO_SUCH_TABLE, errorcode.ER_BAD_FIELD_ERROR):
                self.garantir_estrutura_bd()
                return executar_consulta()
            raise
