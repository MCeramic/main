# cd C:\Users\Weronika\Desktop\Anna\bot\project\facebook
# python -m venv venv
# .\venv\Scripts\activate

import json
import os

# Mapowanie stron do intencji i produktów (pozostaje bez zmian)
page_to_intent_products = {
    2: {
        "intent": "SYSTEM ŁAZIENKOWY Umiarkowane obciążenie wilgocią. Uszczelnienie zespolone",
        "products": ["ARDEX AM 100", "ARDEX 8+9", "ARDEX SK 12", "ARDEX X 7 G PLUS", "ARDEX G 10 PREMIUM", "ARDEX SE"]
    },
    3: {
        "intent": "SYSTEM ŁAZIENKOWY Umiarkowane obciążenie wilgocią. Mata uszczelniająca",
        "products": ["ARDEX AM 100", "ARDEX X 7 G PLUS", "ARDEX 7+8", "ARDEX G 10 PREMIUM", "ARDEX SK 12", "ARDEX SK 100 W", "ARDEX SE"]
    },
    4: {
        "intent": "OKŁADZINY WIELKOFORMATOWE Jastrych cementowy wewnątrz pomieszczeń",
        "products": ["ARDEX P 52", "ARDEX CL 100", "ARDEX COLAFIX 8X8", "ARDEX G 10 PREMIUM", "ARDEX SE"]
    },
    5: {
        "intent": "OKŁADZINY WIELKOFORMATOWE Jastrych anhydrytowy wewnątrz pomieszczeń",
        "products": ["ARDEX P 52", "ARDEX S 28 NEU", "ARDEX G 10 PREMIUM", "ARDEX SE"]
    },
    6: {
        "intent": "KAMIEN NATURALNY (wrażliwy na wilgoć) Wewnątrz pomieszczeń",
        "products": ["ARDEX P 52", "ARDEX CL 100", "ARDEX N 23", "ARDEX N 23 W", "ARDEX G 10 PREMIUM", "ARDEX C1 100"]
    },
    7: {
        "intent": "KAMIEN NATURALNY (niewrażliwy na wilgoć) Wewnątrz pomieszczeń",
        "products": ["ARDEX P 52", "ARDEX CL 100", "ARDEX X 7 G PLUS", "ARDEX X 7 W PLUS", "ARDEX G 10 PREMIUM", "ARDEX ST"]
    },
    8: {
        "intent": "KAMIEN NATURALNY (niewrażliwy na wilgoć) Na zewnątrz pomieszczeń",
        "products": ["ARDEX AM 100", "ARDEX 8+9", "ARDEX SK 12", "ARDEX X 32", "ARDEX X 7 G PLUS", "ARDEX G 10 PREMIUM", "ARDEX SE"]
    },
    9: {
        "intent": "SYSTEM TARASOWO BALKONOWY Uszczelnienie zespolone",
        "products": ["ARDEX AM 100", "ARDEX 8+9", "ARDEX SK 12", "ARDEX X 7 G PLUS", "ARDEX G 10 PREMIUM", "ARDEX SE"]
    },
    10: {
        "intent": "SYSTEM BASENOWY",
        "products": ["ARDEX A 38", "ARDEX AM 100", "ARDEX A 46", "ARDEX S 7 PLUS", "ARDEX SK 12", "ARDEX X 7 G PLUS", "ARDEX X 77 W", "ARDEX RG 12 1-6", "ARDEX G 10 PREMIUM"]
    },
    11: {
        "intent": "SYSTEM KLEJENIA Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Ściana poza prysznicem",
        "products": ["ARDEX A 45", "ARDEX AF 181 W", "ARDEX SC"]
    },
    12: {
        "intent": "SYSTEM KLEJENIA Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Ściana pod prysznicem",
        "products": ["ARDEX A 45", "ARDEX FIX", "ARDEX SK 100 W", "ARDEX AF 181 W", "ARDEX SC"]
    },
    13: {
        "intent": "SYSTEM KLEJENIA Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Podłoga poza prysznicem",
        "products": ["ARDEX A 45 FEIN", "ARDEX K 60", "ARDEX SK 100 W", "ARDEX AF180", "ARDEX 181 W", "ARDEX SC"]
    },
    14: {
        "intent": "SYSTEM KLEJENIA Dekoracyjnych wykładzin LVT",
        "products": ["ARDEX P 4 READY", "ARDEX CL 100", "ARDEX AF 1140", "ARDEX AF 155"]
    },
    15: {
        "intent": "SYSTEM KLEJENIA Okładzin drewnianych",
        "products": ["ARDEX A 45 FEIN", "ARDEX PU 30", "ARDEX AF 460", "ARDEX AF 480"]
    },
    16: {
        "intent": "SYSTEM KLEJENIA Wykładzin dywanowych",
        "products": ["ARDEX P 52", "ARDEX CL 100", "ARDEX AF 230"]
    }
}

# Wczytanie danych produktów z products.json
def load_products_data():
    products_data = {}
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            products_list = json.load(f)
            for product in products_list:
                products_data[product["name"]] = product
    except FileNotFoundError:
        print("Plik products.json nie istnieje. Używam domyślnych danych.")
    return products_data

# Wczytaj pełne dane o produktach z products.json
existing_products_data = load_products_data()

# Struktura produktów bez instrukcji
products = []
for page_num, data in page_to_intent_products.items():
    for product_name in data["products"]:
        # Sprawdź, czy produkt istnieje w products.json
        if product_name in existing_products_data:
            # Użyj istniejących danych produktu, usuwając instrukcje
            product = existing_products_data[product_name].copy()
            if "instructions" in product:
                del product["instructions"]
        else:
            # Utwórz nowy produkt z podstawowymi danymi, bez instrukcji
            product = {
                "name": product_name,
                "description": f"Brak szczegółowego opisu – {product_name} to produkt ARDEX do zastosowań budowlanych."
            }
        
        products.append(product)

# Usunięcie duplikatów produktów
unique_products = {}
for product in products:
    name = product["name"]
    if name not in unique_products:
        unique_products[name] = product

# Konwersja na listę
final_products = list(unique_products.values())

# Zapis do products.json
output_file = "products.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_products, f, ensure_ascii=False, indent=4)

print(f"Wygenerowano {output_file} z {len(final_products)} unikalnymi produktami.")