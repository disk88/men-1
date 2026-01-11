import os
import json
import gspread
from google.oauth2.service_account import Credentials
import urllib.request
from PIL import Image

# Configurazione
SHEET_ID = "1wKMa0cmpQVWNmzYb9y3oTB5lpuEIa8GTXdYqiG3836c"
PROMO_PATH = "promo_static.jpg"
LOG_PATH = "current_promo_url.txt"

def get_drive_direct_url(url):
    if "drive.google.com" in url:
        # Estrae l'ID del file dal link di Google Drive
        fid = url.split('/')[-2] if '/d/' in url else url.split('id=')[-1].split('&')[0]
        return f"https://drive.google.com/uc?export=download&id={fid}"
    return url

def update_sheet_status(status, message):
    try:
        # Carica le chiavi dal "Secret" che hai salvato su GitHub
        creds_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Apri lo sheet
        sheet = client.open_by_key(SHEET_ID).worksheet("Impostazioni")
        
        # Trova la riga "Immagine Promo" e scrivi nella colonna D (la quarta)
        cell = sheet.find("Immagine Promo")
        sheet.update_cell(cell.row, 4, f"{status}: {message}")
        print(f"Stato aggiornato sullo Sheet: {status}")
    except Exception as e:
        print(f"Impossibile aggiornare lo Sheet: {e}")

try:
    # 1. Leggi lo Sheet per vedere cosa ha inserito l'utente
    creds_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    creds = Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet("Impostazioni")
    
    records = sheet.get_all_records()
    promo_url = ""
    for r in records:
        if r.get('Proprietà') == 'Immagine Promo':
            promo_url = r.get('Valore')
            break

    # 2. Gestione Immagine
    if promo_url:
        print(f"Download immagine da: {promo_url}")
        direct_url = get_drive_direct_url(promo_url)
        
        # Scarica temporaneamente
        urllib.request.urlretrieve(direct_url, "temp.jpg")
        
        # Ottimizza con Pillow
        img = Image.open("temp.jpg")
        img = img.convert("RGB") # Converte in formato standard
        img.save(PROMO_PATH, "JPEG", quality=85, optimize=True)
        
        # Salva l'URL corrente in un file di testo per il controllo del sito
        with open(LOG_PATH, "w") as f:
            f.write(promo_url)
            
        os.remove("temp.jpg")
        update_sheet_status("🟢 SUCCESS", "Immagine caricata correttamente")
    else:
        # Se non c'è URL, rimuovi i file esistenti
        if os.path.exists(PROMO_PATH): os.remove(PROMO_PATH)
        if os.path.exists(LOG_PATH): os.remove(LOG_PATH)
        update_sheet_status("⚪ EMPTY", "Nessuna promo attiva")

except Exception as e:
    print(f"Errore generale: {e}")
    update_sheet_status("🔴 ERROR", str(e))
