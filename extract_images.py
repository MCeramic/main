# cd C:\Users\Weronika\Desktop\Anna\bot\project\facebook
# python -m venv venv
# .\venv\Scripts\activate
# python extract_images.py

import fitz  # PyMuPDF
import os
import json

pdf_path = "rozwiazania-systemowe-ardex.pdf"  # Ścieżka do PDF-a
output_dir = os.path.dirname(os.path.abspath("products.json"))  # Katalog z products.json

# Wczytanie products.json
with open("products.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Mapowanie stron PDF na intencje
page_to_intent = {
    5: "SYSTEM ŁAZIENKOWY | Umiarkowane obciążenie wilgocią. Uszczelnienie zespolone",
    6: "SYSTEM ŁAZIENKOWY | Umiarkowane obciążenie wilgocią. Mata uszczelniająca",
    7: "OKŁADZINY WIELKOFORMATOWE | Jastrych cementowy wewnątrz pomieszczeń",
    8: "OKŁADZINY WIELKOFORMATOWE | Jastrych anhydrytowy wewnątrz pomieszczeń",
    9: "KAMIEN NATURALNY (wrażliwy na wilgoć) | Wewnątrz pomieszczeń",
    10: "KAMIEN NATURALNY (niewrażliwy na wilgoć) | Wewnątrz pomieszczeń",
    11: "KAMIEN NATURALNY (niewrażliwy na wilgoć) | Na zewnątrz pomieszczeń",
    12: "SYSTEM TARASOWO BALKONOWY | Uszczelnienie zespolone",
    13: "SYSTEM BASENOWY",
    14: "SYSTEM KLEJENIA | Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Ściana poza prysznicem",
    15: "SYSTEM KLEJENIA | Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Ściana pod prysznicem",
    16: "SYSTEM KLEJENIA | Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Podłoga poza prysznicem",
    17: "SYSTEM KLEJENIA | Dekoracyjnych wykładzin LVT",
    18: "SYSTEM KLEJENIA | Okładzin drewnianych",
    19: "SYSTEM KLEJENIA | Wykładzin dywanowych"
}

doc = fitz.open(pdf_path)
print(f"Liczba stron w dokumencie: {doc.page_count}")

for page_num, data in page_to_intent_products.items():
    intent = data["intent"]
    intent_normalized = intent.lower().replace(" ", "_").replace("|", "").replace("(", "").replace(")", "").replace(".", "").replace("ł", "l").replace("ę", "e").replace("ą", "a").replace("ś", "s").replace("ć", "c").replace("ń", "n").replace("ó", "o").replace("ż", "z").replace("ź", "z")
    image_filename = f"{intent_normalized}.png"
    
    if page_num > doc.page_count:
        print(f"Strona {page_num} przekracza liczbę stron w dokumencie ({doc.page_count})! Pomijam.")
        continue
    
    page = doc[page_num - 1]  # Odejmujemy 1, bo fitz indeksuje od 0
    print(f"Strona {page_num} - Wymiary: {page.rect.width} x {page.rect.height} punktów")
    
    zoom = 5
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)
    
    print(f"Strona {page_num} - Wymiary obrazu: {pix.width} x {pix.height} pikseli")
    
    image_path = os.path.join(output_dir, image_filename)
    pix.save(image_path)
    print(f"Zapisano renderowany obraz: {image_path}")

doc.close()