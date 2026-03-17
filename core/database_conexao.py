import os
from dotenv import load_dotenv
import mysql.connector
from core.models import Duelistas

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Conexao:
    def __init__(self):
        # Utiliza as variáveis de ambiente, com valores padrão caso não encontre
        self.host = os.getenv("DB_HOST", "127.0.0.1")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "root")
        self.database = os.getenv("DB_NAME", "torneio")

    def conectar_bd(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

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

    def listar_duelistas(self):
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor(dictionary=True)
            sql = "SELECT * FROM duelistas WHERE ativo = 1"
            cursor.execute(sql)
            duelistas = cursor.fetchall()
            return duelistas
        finally:
            conexao.close()

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

    def carregar_duelistas(self):

        dados = self.listar_duelistas()
        
        lista_duelistas = []
        for data in dados:
            duelista = Duelistas(
                nome=data['nome'],
                vitorias=int(data['vitorias']),
                derrotas=int(data['derrotas']),
                empates=int(data['empates']),
            )
            duelista.participacao = int(data['participacao'])
            lista_duelistas.append(duelista)
        
        return lista_duelistas
    
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
        conexao = self.conectar_bd()
        try:
            cursor = conexao.cursor(dictionary=True)
            sql = """
                SELECT tp.id as tp_id, d.nome, d.ativo, tp.vitorias, tp.derrotas, tp.empates, tp.pontos_obtidos
                FROM torneio_participantes tp
                JOIN duelistas d ON tp.duelista_id = d.id
                WHERE tp.torneio_id = %s
                ORDER BY tp.pontos_obtidos DESC, tp.vitorias DESC
            """
            cursor.execute(sql, (torneio_id,))
            return cursor.fetchall()
        finally:
            conexao.close()
            
    def adicionar_participante_torneio(self, torneio_id, nome, vitorias, derrotas, empates):
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
                    SET vitorias = %s, derrotas = %s, empates = %s, pontos_obtidos = %s
                    WHERE id = %s
                """, (vitorias, derrotas, empates, pontos_torneio_novos, hist_torneio['id']))
                
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
                    INSERT INTO torneio_participantes (torneio_id, duelista_id, vitorias, derrotas, empates, pontos_obtidos)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (torneio_id, duelista['id'], vitorias, derrotas, empates, pontos_torneio_novos))
                
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
