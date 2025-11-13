import threading
import time
from flask import Flask
from flask_socketio import SocketIO
import psutil # A biblioteca para obter os dados do sistema

app = Flask(__name__)
# Configura o SocketIO com CORS (Cross-Origin Resource Sharing)
# Permite que o index.html acesse este servidor
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Variáveis para a thread de monitoramento ---
thread = None
thread_lock = threading.Lock()

def obter_dados_do_sistema():
    """
    Coleta os dados de CPU, Memória e Disco e os emite
    para os clientes a cada 1 segundo, em loop.
    """
    
    # psutil.cpu_percent(interval=None) pega o uso desde a última chamada
    # Chamamos uma vez no início (com um pequeno intervalo) para "zerar"
    psutil.cpu_percent(interval=0.1) 
    
    while True:
        # 1. Coleta os dados
        cpu_percent = psutil.cpu_percent(interval=None) # Pega o uso de CPU
        mem_percent = psutil.virtual_memory().percent # Pega o uso de memória
        disk_percent = psutil.disk_usage('/').percent # Pega o uso de disco (partição principal)

        # 2. "Emite" (envia) os dados para todos os clientes conectados
        # O nome do "evento" que o cliente vai escutar é 'system_update'
        socketio.emit('system_update', {
            'cpu': cpu_percent,
            'mem': mem_percent,
            'disk': disk_percent
        })
        
        # 3. Espera 1 segundo antes de enviar a próxima atualização
        socketio.sleep(1)

@socketio.on('connect')
def handle_connect():
    """
    Chamado quando um novo cliente (o HTML) se conecta ao servidor.
    """
    global thread
    print("Cliente conectado!")
    
    # Garante que a thread (o loop de monitoramento) seja iniciada
    # apenas uma vez, pelo primeiro cliente que se conectar.
    with thread_lock:
        if thread is None:
            # Inicia a função 'obter_dados_do_sistema' em segundo plano
            thread = socketio.start_background_task(target=obter_dados_do_sistema)

# Rota HTTP apenas para mostrar que o servidor está no ar
@app.route('/')
def index():
    return "Servidor de monitoramento está no ar. Conecte-se via WebSocket."

if __name__ == '__main__':
    print("Iniciando servidor em http://localhost:5000")
    # debug=True faz o servidor reiniciar se você alterar o código
    # allow_unsafe_werkzeug=True é necessário para o modo de debug com SocketIO
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)