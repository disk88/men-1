import os
import json
import gspread
from google.oauth2.service_account import Credentials
import urllib.request
from PIL import Image

# Configurazione
SHEET_ID = "1wKMa0cmpQVWNmzYb9y3oTB5lpuEIa8GTXdYqiG3836c"

# Mappatura: Cosa cercare nello Sheet -> Nome file da salvare su GitHub
TASKS = {
    "Logo URL": "logo_static.jpg",
    "Immagine Promo": "promo_static.jpg"
}

def get_drive_direct_url(url):
    if "drive.google.com" in url:
        fid = url.split('/')[-2] if '/d/' in url else url.split('id=')[-1].split('&')[0]
        return f"https://drive.google.com/uc?export=download&id={fid}"
    return url

def process_media(sheet, label, filename):
    try:
        # Trova la cella con l'etichetta (es. "Logo URL")
        cell = sheet.find(label)
        row = cell.row
        # Il link è nella colonna B (2), il feedback andrà nella colonna C (3)
        url = sheet.cell(row, 2).value
        
        if url and url.strip():
            print(f"Elaborazione {label}: {url}")
            direct_url = get_drive_direct_url(url)
            
            # Download e Ottimizzazione
            urllib.request.urlretrieve(direct_url, "temp_img")
            img = Image.open("temp_img").convert("RGB")
            
            # Ridimensionamento intelligente per non pesare sui dispositivi
            if img.width > 1920:
                img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            
            img.save(filename, "JPEG", quality=85, optimize=True)
            
            # Crea un file .txt con l'URL originale per il controllo di sincronizzazione del sito
            with open(f"{filename}.txt", "w") as f:
                f.write(url)
            
            os.remove("temp_img")
            sheet.update_cell(row, 3, "🟢 SUCCESS")
        else:
            # Se il link è vuoto, rimuoviamo i file vecchi
            if os.path.exists(filename): os.remove(filename)
            if os.path.exists(f"{filename}.txt"): os.remove(f"{filename}.txt")
            sheet.update_cell(row, 3, "⚪ EMPTY")
            
    except Exception as e:
        print(f"Errore su {label}: {e}")
        try:
            cell = sheet.find(label)
            sheet.update_cell(cell.row, 3, f"🔴 ERROR")
        except:
            pass

def main():
    if 'GOOGLE_CREDENTIALS' not in os.environ:
        print("Errore: Credenziali non trovate nei Secrets di GitHub")
        return

    # Autenticazione
    creds_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SHEET_ID).worksheet("Impostazioni")

    # Esegui per ogni elemento configurato (Logo e Promo)
    for label, filename in TASKS.items():
        process_media(sheet, label, filename)

if __name__ == "__main__":
    main()
