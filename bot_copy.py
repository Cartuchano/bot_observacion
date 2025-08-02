import json
import time
import websocket
import os
from datetime import datetime

# ==============================
# Cargar lista de vaults top 10
# ==============================
with open("vaults_top10.json", "r") as f:
    vaults_top10 = json.load(f)

print(f"[INFO] Vaults cargados: {vaults_top10}")

# ==============================
# Conectar al WebSocket
# ==============================
def on_open(ws):
    print("[INFO] Conectado al WebSocket, escuchando señales de vaults...")
    # Suscripción al canal (simulación de ejemplo)
    ws.send(json.dumps({"op": "subscribe", "channel": "vault_signals"}))

def on_message(ws, message):
    data = json.loads(message)
    vault = data.get("vault")
    if vault not in vaults_top10:
        return
    
    print(f"[INFO] Señal recibida de vault {vault}: {data}")

def on_close(ws, close_status_code, close_msg):
    print("[INFO] Conexión cerrada con el servidor.")
    print(f"[DEBUG] Código: {close_status_code} | Mensaje: {close_msg}")

def iniciar_bot():
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://api.hyperliquid-testnet.xyz/ws",
                on_open=on_open,
                on_message=on_message,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            print(f"[ERROR] {datetime.now()} | Error en WebSocket: {e}")
            print("[INFO] Reintentando en 20 segundos...")
            time.sleep(20)

# ==============================
# Iniciar el bot en segundo plano
# ==============================
import threading
bot_thread = threading.Thread(target=iniciar_bot, daemon=True)
bot_thread.start()

# ==============================
# Servidor mínimo para Render
# ==============================
from http.server import BaseHTTPRequestHandler, HTTPServer

# Render exige un puerto abierto; usa PORT de la variable de entorno
port = int(os.environ.get("PORT", 8080))

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot running on Render")

print(f"[INFO] Servidor HTTP escuchando en puerto {port} (para Render)...")
server = HTTPServer(("0.0.0.0", port), SimpleHandler)
server.serve_forever()
