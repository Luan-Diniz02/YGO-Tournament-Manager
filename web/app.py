import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from core.models import Duelistas, Torneio
from core.database_conexao import Conexao

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
# Carrega a chave secreta a partir das variáveis de ambiente (com fallback seguro apenas para evitar quebrar bruscamente)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_if_env_not_found')

# Instancia da conexão
conexao = Conexao()

@app.route('/')
def index():
    """Página inicial com menu principal"""
    return render_template('index.html')

@app.route('/cadastrar_torneio', methods=['GET', 'POST'])
def cadastrar_torneio():
    """Página para cadastrar torneios"""
    if request.method == 'POST':
        try:
            nome = request.form['nome_torneio'].strip()
            rodadas = int(request.form['rodadas'])
            duelistas = int(request.form['duelistas'])
            data = request.form['data'].strip()

            if not nome or not data:
                flash('O nome do torneio e a data não podem estar vazios.', 'error')
                return render_template('cadastrar_torneio.html')
            
            if rodadas <= 0 or duelistas <= 0:
                flash('Os valores de rodadas e duelistas devem ser positivos.', 'error')
                return render_template('cadastrar_torneio.html')

            torneio = Torneio(nome, rodadas, duelistas, data)
            torneio_id = conexao.cadastrar_torneio(torneio)
            flash('Torneio cadastrado com sucesso!', 'success')
            return redirect(url_for('painel_torneio', id=torneio_id))

        except ValueError as e:
            flash(f'Erro: {str(e)}', 'error')
            return render_template('cadastrar_torneio.html')
    
    return render_template('cadastrar_torneio.html')

@app.route('/buscar_duelista', methods=['GET', 'POST'])
def buscar_duelista():
    """Página para buscar duelista específico"""
    duelistas = conexao.carregar_duelistas()
    duelistas_ordenados = sorted(duelistas, key=lambda d: d.pontos, reverse=True)
    
    duelista_encontrado = None
    posicao_encontrada = None
    
    if request.method == 'POST':
        nome_busca = request.form['nome_busca'].strip()
        if nome_busca:
            for posicao, duelista in enumerate(duelistas_ordenados, start=1):
                if nome_busca.casefold() == duelista.nome.casefold():
                    duelista_encontrado = duelista
                    posicao_encontrada = posicao
                    break
            
            if not duelista_encontrado:
                flash('Duelista não encontrado!', 'error')
    
    return render_template('buscar_duelista.html', 
                         duelistas=duelistas_ordenados, 
                         duelista_encontrado=duelista_encontrado,
                         posicao_encontrada=posicao_encontrada)

@app.route('/alterar_duelista/<nome>', methods=['GET', 'POST'])
def alterar_duelista(nome):
    """Página para alterar dados de um duelista"""
    lista_duelistas = conexao.carregar_duelistas()
    duelista = None
    
    for d in lista_duelistas:
        if d.nome.casefold() == nome.casefold():
            duelista = d
            break
    
    if not duelista:
        flash('Duelista não encontrado!', 'error')
        return redirect(url_for('buscar_duelista'))
    
    if request.method == 'POST':
        try:
            novo_nome = request.form['nome'].strip()
            vitorias = int(request.form['vitorias'])
            derrotas = int(request.form['derrotas'])
            empates = int(request.form['empates'])

            if not novo_nome:
                flash('O nome do duelista não pode estar vazio.', 'error')
                return render_template('alterar_duelista.html', duelista=duelista)
            
            if vitorias < 0 or derrotas < 0 or empates < 0:
                flash('Os valores de vitórias, derrotas e empates devem ser não negativos.', 'error')
                return render_template('alterar_duelista.html', duelista=duelista)

            # Atualiza os dados do duelista
            nome_antigo = duelista.nome
            duelista.nome = novo_nome
            duelista.vitorias = vitorias
            duelista.derrotas = derrotas
            duelista.empates = empates

            # Atualiza o banco de dados
            conexao.atualizar_registro_duelista(nome_antigo, novo_nome, vitorias, derrotas, empates, duelista.pontos)
            flash('Dados do duelista atualizados com sucesso!', 'success')
            return redirect(url_for('buscar_duelista'))

        except ValueError as e:
            flash(f'Erro: {str(e)}', 'error')
            return render_template('alterar_duelista.html', duelista=duelista)
    
    return render_template('alterar_duelista.html', duelista=duelista)

@app.route('/ranking')
def ranking():
    """Página com o ranking dos duelistas"""
    duelistas = conexao.carregar_duelistas()
    duelistas_ordenados = sorted(duelistas, key=lambda d: d.pontos, reverse=True)
    return render_template('ranking.html', duelistas=duelistas_ordenados)

@app.route('/visualizar_torneios')
def visualizar_torneios():
    """Página para visualizar torneios (buscando do BD)"""
    torneios_bd = conexao.listar_torneios()
    return render_template('visualizar_torneios.html', torneios=torneios_bd)

@app.route('/torneio/<int:id>')
def painel_torneio(id):
    """Página de gerenciamento de um torneio específico"""
    torneio = conexao.get_torneio(id)
    if not torneio:
        flash('Torneio não encontrado!', 'error')
        return redirect(url_for('visualizar_torneios'))
        
    participantes = conexao.listar_participantes_torneio(id)
    todos_duelistas = conexao.carregar_duelistas()
    return render_template('painel_torneio.html', torneio=torneio, participantes=participantes, todos_duelistas=todos_duelistas)

@app.route('/torneio/<int:id>/adicionar_jogador', methods=['POST'])
def adicionar_jogador_torneio(id):
    """Rota invisível para processar a adição de um jogador ao torneio"""
    nome = request.form['nome_duelista'].strip()
    vitorias = int(request.form['vitorias'])
    derrotas = int(request.form['derrotas'])
    empates = int(request.form['empates'])
    
    if not nome:
        flash('O nome do duelista não pode estar vazio.', 'error')
    elif vitorias < 0 or derrotas < 0 or empates < 0:
        flash('Os valores devem ser não negativos.', 'error')
    else:
        try:
            conexao.adicionar_participante_torneio(id, nome, vitorias, derrotas, empates)
            flash(f'Participação de {nome} registrada com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao registrar participante: {str(e)}', 'error')

    return redirect(url_for('painel_torneio', id=id))

@app.route('/desativar_duelista/<nome>', methods=['POST'])
def desativar_duelista(nome):
    """Manda o duelista para lista de inativos (soft-delete)"""
    try:
        conexao.desativar_duelista(nome)
        flash(f'Duelista {nome} foi inativado! Seu histórico permanecerá nos torneios, mas ele ocultado do Ranking atual.', 'success')
    except Exception as e:
        flash(f'Erro ao inativar duelista {nome}: {str(e)}', 'error')
    
    return redirect(url_for('buscar_duelista'))

@app.route('/excluir_torneio/<int:id>', methods=['POST'])
def excluir_torneio(id):
    """Exclui um torneio"""
    try:
        conexao.excluir_torneio(id)
        flash('Torneio excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir torneio: {str(e)}', 'error')
    
    return redirect(url_for('visualizar_torneios'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)