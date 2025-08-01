# Prueba de reintento de Render

import json
import websocket
import time
from datetime import datetime, timedelta

# ===============================
# CONFIGURACIÓN DEL BOT
# ===============================

with open("vaults_top10.json", "r") as f:
    vaults_top10 = [v["name"] for v in json.load(f)]

CONSENSO_MINIMO = 2
VENTANA_TIEMPO = 15 * 60  # 15 min
WS_URL = "wss://api.hyperliquid-testnet.xyz/ws"
LOG_FILE = "senales.log"

# ===============================
# COLORES PARA PANTALLA
# ===============================
COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"    # LONG
COLOR_RED = "\033[91m"      # SHORT
COLOR_YELLOW = "\033[93m"   # CONSENSO

# ===============================
# Variables de estado
# ===============================
historial_senales = {}  # clave: (par, lado) -> [(timestamp, vault)]

def guardar_log(texto):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(texto + "\n")

def imprimir_coloreado(texto, color):
    """Imprime con color en pantalla y también guarda en log sin color"""
    print(color + texto + COLOR_RESET)
    guardar_log(texto)

def on_message(ws, message):
    try:
        data = json.loads(message)
        if "vaultSignals" in data:
            señales = data["vaultSignals"]

            for s in señales:
                vault = s["vaultName"]
                if vault not in vaults_top10:
                    continue  # ignoramos vaults que no están en el top 10

                par = s["symbol"]
                lado = s["side"]
                clave = (par, lado)
                ahora = datetime.now()

                # Mostrar todas las señales en color
                color = COLOR_GREEN if lado == "LONG" else COLOR_RED
                texto = f"[SEÑAL] {ahora} | Vault: {vault} | {par} {lado}"
                imprimir_coloreado(texto, color)

                # Limpiar señales antiguas de la misma clave
                if clave in historial_senales:
                    historial_senales[clave] = [
                        (t, v) for t, v in historial_senales[clave]
                        if ahora - t <= timedelta(seconds=VENTANA_TIEMPO)
                    ]
                else:
                    historial_senales[clave] = []

                # Añadimos la nueva señal con el vault
                historial_senales[clave].append((ahora, vault))

                # Si alcanza consenso, mostramos bloque
                if len(historial_senales[clave]) >= CONSENSO_MINIMO:
                    vaults_coincidentes = [v for _, v in historial_senales[clave]]

                    bloque = (
                        "\n" + "="*50 + "\n" +
                        f"🔥 [CONSENSO] {ahora}\n"
                        f"{par} {lado} detectado {len(historial_senales[clave])} veces "
                        f"en {VENTANA_TIEMPO/60} min\n"
                        f"Vaults: {', '.join(set(vaults_coincidentes))}\n" +
                        "="*50
                    )
                    imprimir_coloreado(bloque, COLOR_YELLOW)

    except Exception as e:
        print("[ERROR] Procesando mensaje:", e)

def on_error(ws, error):
    print("[ERROR] WebSocket:", error)

def on_close(ws, close_status_code, close_msg):
    print("[INFO] Conexión cerrada con el servidor.")

def on_open(ws):
    print("[INFO] Conectado al WebSocket, escuchando señales...")
    guardar_log(f"[INFO] {datetime.now()} | Conectado al WebSocket")
    suscripcion = {"method": "subscribe", "channels": [{"name": "vaultSignals"}]}
    ws.send(json.dumps(suscripcion))

def iniciar_bot():
    while True:
        try:
            ws = websocket.WebSocketApp(
                WS_URL,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            ws.run_forever()
        except Exception as e:
            print(f"[ERROR] {datetime.now()} | {e}")
            guardar_log(f"[ERROR] {datetime.now()} | Reconexión en 20s: {e}")
        print("[INFO] Reintentando conexión en 20 segundos...")
        time.sleep(20)

if __name__ == "__main__":
    iniciar_bot()
