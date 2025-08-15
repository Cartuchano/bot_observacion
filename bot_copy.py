import os
import json
import time
import requests
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Guardar credenciales desde variable de entorno a archivo temporal
credenciales = os.environ.get("GOOGLE_CREDENTIALS")
with open("credenciales_google.json", "w") as f:
    f.write(credenciales)

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales_google.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Señales Hyperliquid")
sheet = spreadsheet.worksheet("Hoja 1")

# Cargar lista de vaults
with open("vaults_top10.json", "r") as f:
    vaults_top10 = json.load(f)

def obtener_senal(vault):
    try:
        url = f"https://api.hyperliquid.xyz/info"
        body = {"type": "vaultState", "user": vault}
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
        sheet.append_row([fecha, vault, simbolo, tipo])
        print(f"[✅ GUARDADO] Señal guardada en Google Sheets: {vault} - {simbolo} - {tipo}")
    except Exception as e:
        print(f"[❌ ERROR] No se pudo guardar la señal en Google Sheets: {e}")

def iniciar_bot():
    print("[🤖 BOT ACTIVO] Observando señales coincidentes de los vaults top 10...")

    while True:
        senales_actuales = []

for vault in vaults_top10:
    nombre_vault = vault["name"] if isinstance(vault, dict) else vault
    senal = obtener_senal(nombre_vault)
    if senal:
        senales_actuales.append((nombre_vault, *senal))


        # Contar coincidencias
        conteo = {}
        for _, simbolo, tipo in senales_actuales:
            clave = (simbolo, tipo)
            conteo[clave] = conteo.get(clave, 0) + 1

        for vault, simbolo, tipo in senales_actuales:
            clave = (simbolo, tipo)
            if conteo[clave] >= 3:
                fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[📡 COINCIDENCIA] {vault} - {simbolo} - {tipo}")
                guardar_senal_en_google_sheets(fecha, vault, simbolo, tipo)

        time.sleep(30)

if __name__ == "__main__":
    iniciar_bot()
