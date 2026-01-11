import os
import json
import gspread
from google.oauth2.service_account import Credentials
import urllib.request
from PIL import Image

# Configurazione
SHEET_ID = "1wKMa0cmpQVWNmzYb9y3oTB5lpuEIa8GTXdYqiG3836c"

# Mappatura: Etichetta nello Sheet -> Nome file finale
TASKS = {
    "Logo URL": "logo_static.png",
    "Immagine Promo": "promo_static.jpg"
}

def get_drive_direct_url(url):
    if "drive.google.com" in url:
        fid = url.split('/')[-2] if '/d/' in url else url.split('id=')[-1].split('&')[0]
        return f"https://drive.google.com/uc?export=download&id={fid}"
    return url

def process_media(sheet, label, filename):
    try:
        cell = sheet.find(label)
        row = cell.row
        url = sheet.cell(row, 2).value # Colonna B
        
        if url and url.strip():
            print(f"Elaborazione {label}: {url}")
            direct_url = get_drive_direct_url(url)
            
            urllib.request.urlretrieve(direct_url, "temp_img")
            img = Image.open("temp_img")
            
            # Ridimensionamento intelligente (max 1920px)
            if img.width > 1920:
                img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            
            if "Logo" in label:
                # Salva in PNG per preservare la trasparenza
                img.save(filename, "PNG", optimize=True)
            else:
                # Salva in JPG per leggerezza (converte in RGB per sicurezza)
                img = img.convert("RGB")
                img.save(filename, "JPEG", quality=85, optimize=True)
            
            # Crea il file di testo per il controllo "anti-lag"
            with open(f"{filename}.txt", "w") as f:
                f.write(url)
            
            os.remove("temp_img")
            sheet.update_cell(row, 3, "🟢 SUCCESS") # Colonna C
        else:
            # Pulizia se il link viene rimosso
            if os.path.exists(filename): os.remove(filename)
            if os.path.exists(f"{filename}.txt"): os.remove(f"{filename}.txt")
            sheet.update_cell(row, 3, "⚪ EMPTY")
            
    except Exception as e:
        print(f"Errore su {label}: {e}")
        try:
            cell = sheet.find(label)
            sheet.update_cell(cell.row, 3, f"🔴 ERROR")
        except: pass

def main():
    if 'GOOGLE_CREDENTIALS' not in os.environ: return
    creds_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet("Impostazioni")

    for label, filename in TASKS.items():
        process_media(sheet, label, filename)

if __name__ == "__main__":
    main()
