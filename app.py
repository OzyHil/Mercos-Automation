from flask import Flask, render_template, request
from flask import send_file
from flask_socketio import SocketIO
from datetime import datetime
from scraping.mercos_data_pedido_flask import main, save_csv 
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/buscar', methods=['POST'])
def buscar():
    global dados_global, file_path_global, data_inicio, data_fim

    data_inicio = request.form['data_inicio']
    data_fim = request.form['data_fim']
    empresa = request.form['empresa']
    
    data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").strftime("%d/%m/%Y")
    data_fim = datetime.strptime(data_fim, "%Y-%m-%d").strftime("%d/%m/%Y")
    file_path_global = f"{empresa}_{data_inicio}_a_{data_fim}".replace("/", "-")

    def emitir_progresso(percent, total=0):
        socketio.emit('progresso', {'percent': percent, 'totalPedidos': total, "nomeArquivo": f'{file_path_global}.csv'})
    
    dados_global = main(empresa, data_inicio, data_fim, progress_callback=emitir_progresso)

    return "Busca finalizada"

@app.route("/baixar/csv", methods=["POST"])
def baixar_html():
    global dados_global, file_path_global

    if not dados_global:
        return "Nenhum dado para baixar", 400
    
    # Verifica se o arquivo já existe para decidir se inclui cabeçalho
    write_header = not os.path.exists(file_path_global + ".csv")

    # Salva os dados no CSV
    save_csv(dados_global, f'data/{file_path_global}', write_header)

    # Envia o arquivo como download
    return send_file(f"data/{file_path_global}.csv", as_attachment=True)

if __name__ == "__main__":
    socketio.run(app, debug=True)
