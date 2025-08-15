import os
import json
import time
import requests
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === 1. GUARDAR CREDENCIALES DESDE VARIABLE DE ENTORNO A ARCHIVO TEMPORAL ===
credenciales = os.environ.get("GOOGLE_CREDENTIALS")

with open("credenciales_google.json", "w") as f:
    f.write(credenciales)

# === 2. CONFIGURAR ACCESO A GOOGLE SHEETS ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credenciales_google.json", scope)
client = gspread.authorize(credentials)

spreadsheet = client.open("Señales Hyperliquid")  # ← Asegúrate de que el nombre coincide exactamente
sheet = spreadsheet.worksheet("Hoja 1")           # ← También asegúrate del nombre de la hoja

# === 3. CARGAR LISTA DE VAULTS ===
with open("vaults_top10.json", "r") as f:
    vaults_top10 = json.load(f)

# === 4. FUNCIONES PRINCIPALES ===
def obtener_senal(vault):
    try:
        url = "https://api.hyperliquid.xyz/info"
        body = {"type": "vaultState", "user": vault["name"]}
        response = requests.post(url, json=body)
        data = response.json()

        if "vaults" not in data or not data["vaults"]:
            return None

        open_positions = data["vaults"][0].get("openPositions", [])
        if not open_positions:
            return None

        simbolo = open_positions[0]["coin"]
        tipo = open_positions[0]["side"]

        return simbolo, tipo
    except Exception as e:
        print(f"[❌ ERROR] No se pudo obtener la señal para {vault}: {e}")
        return None

def guardar_senal_en_google_sheets(fecha, vault, simbolo, tipo):
    try:
        sheet.append_row([fecha, vault["name"], simbolo, tipo])
        print(f"[✅ GUARDADO] Señal guardada en Google Sheets: {vault['name']} - {simbolo} - {tipo}")
    except Exception as e:
        print(f"[❌ ERROR] No se pudo guardar la señal en Google Sheets: {e}")

def iniciar_bot():
    print("[🤖 BOT ACTIVO] Observando señales coincidentes de los vaults top 10...")

    while True:
        senales_actuales = []

        for vault in vaults_top10:
            senal = obtener_senal(vault)
            if senal:
                senales_actuales.append((vault, *senal))

        # Contar coincidencias
        conteo = {}
        for _, simbolo, tipo in senales_actuales:
            clave = (simbolo, tipo)
            conteo[clave] = conteo.get(clave, 0) + 1

        for vault, simbolo, tipo in senales_actuales:
            clave = (simbolo, tipo)
            if conteo[clave] >= 3:
                fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[📡 COINCIDENCIA] {vault['name']} - {simbolo} - {tipo}")
                guardar_senal_en_google_sheets(fecha, vault, simbolo, tipo)

        time.sleep(30)

# === 5. INICIO DEL BOT ===
if __name__ == "__main__":
    iniciar_bot()
