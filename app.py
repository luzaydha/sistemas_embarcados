import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS # Importar o CORS

# --- Configuração Inicial ---
app = Flask(__name__)
# Habilitar CORS para que o index.html possa fazer requisições
# para este servidor (que roda em http://localhost:5000)
CORS(app) 

DB_NAME = 'todo.db'

# --- Funções do Banco de Dados (SQLite) ---

def get_db_connection():
    """Cria uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    # Retorna linhas como dicionários (mais fácil de converter para JSON)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Cria a tabela de tarefas se ela não existir."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            concluida BOOLEAN NOT NULL CHECK (concluida IN (0, 1))
        )
    ''')
    conn.commit()
    conn.close()

# --- Rotas da API (CRUD) ---

@app.route('/tarefas', methods=['GET'])
def get_tarefas():
    """R (READ): Retorna todas as tarefas."""
    conn = get_db_connection()
    cursor = conn.execute('SELECT id, descricao, concluida FROM tarefas ORDER BY id DESC')
    tarefas = cursor.fetchall()
    conn.close()
    
    # Converte o resultado (sqlite3.Row) para uma lista de dicionários
    lista_tarefas = [dict(tarefa) for tarefa in tarefas]
    
    # Converte o booleano (0/1) para (False/True) para o JSON
    for tarefa in lista_tarefas:
        tarefa['concluida'] = bool(tarefa['concluida'])
        
    return jsonify(lista_tarefas)

@app.route('/tarefas', methods=['POST'])
def add_tarefa():
    """C (CREATE): Adiciona uma nova tarefa."""
    data = request.json
    
    if not data or 'descricao' not in data:
        return jsonify({'erro': 'Descrição da tarefa é obrigatória'}), 400
        
    descricao = data['descricao']
    
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO tarefas (descricao, concluida) VALUES (?, ?)',
                          (descricao, 0)) # Novas tarefas começam como não concluídas
    conn.commit()
    
    nova_id = cursor.lastrowid
    
    # Retorna a tarefa recém-criada
    nova_tarefa = conn.execute('SELECT * FROM tarefas WHERE id = ?', (nova_id,)).fetchone()
    conn.close()

    tarefa_dict = dict(nova_tarefa)
    tarefa_dict['concluida'] = bool(tarefa_dict['concluida'])
    
    return jsonify(tarefa_dict), 201 # 201 Created

@app.route('/tarefas/<int:id>', methods=['PUT'])
def update_tarefa(id):
    """U (UPDATE): Atualiza o status (concluída) de uma tarefa."""
    data = request.json
    
    if 'concluida' not in data:
        return jsonify({'erro': 'Status "concluida" é obrigatório'}), 400
    
    concluida = data['concluida']
    # Converte o booleano do JSON (True/False) para Inteiro do SQLite (1/0)
    concluida_int = 1 if concluida else 0 
    
    conn = get_db_connection()
    cursor = conn.execute('UPDATE tarefas SET concluida = ? WHERE id = ?',
                          (concluida_int, id))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'erro': 'Tarefa não encontrada'}), 404
        
    # Retorna a tarefa atualizada
    tarefa_atualizada = conn.execute('SELECT * FROM tarefas WHERE id = ?', (id,)).fetchone()
    conn.close()

    tarefa_dict = dict(tarefa_atualizada)
    tarefa_dict['concluida'] = bool(tarefa_dict['concluida'])
    
    return jsonify(tarefa_dict)

@app.route('/tarefas/<int:id>', methods=['DELETE'])
def delete_tarefa(id):
    """D (DELETE): Deleta uma tarefa."""
    conn = get_db_connection()
    cursor = conn.execute('DELETE FROM tarefas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    if cursor.rowcount == 0:
        return jsonify({'erro': 'Tarefa não encontrada'}), 404

    return jsonify({'mensagem': 'Tarefa deletada com sucesso'})

# --- Inicialização ---
if __name__ == '__main__':
    init_db() # Garante que a tabela exista antes de rodar o app
    app.run(debug=True, port=5000)