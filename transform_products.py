# cd C:\Users\Weronika\Desktop\Anna\bot\project\facebook
# python -m venv venv
# .\venv\Scripts\activate
# transform_products.py

import json
import re

# Wczytanie istniejącego products.json
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lines = data["lines"]

# Parsowanie produktów
products = []
current_product = None
inside_technical_data = False  # Flaga oznaczająca sekcję "dane techniczne"

for line in lines:
    line = line.strip()
    
    if line == "":  # Pusta linia oznacza nowy produkt
        if current_product:
            products.append(current_product)
        current_product = None
        inside_technical_data = False  # Resetujemy flagę
    else:
        if current_product is None:
            # Pierwsza linia to nazwa produktu
            current_product = {
                "name": line,
                "description": "",
                "dane techniczne": {}
            }
        elif line.startswith("Opis:"):
            # Dodaj opis produktu
            current_product["description"] = line.replace("Opis:", "").strip()
        elif re.match(r"ARDEX\s+\w+", line):
            # Nowy produkt - zamykamy obecny i zaczynamy nowy
            if current_product:
                products.append(current_product)
            current_product = {
                "name": line,
                "description": "",
                "dane techniczne": {}
            }
            inside_technical_data = False  # Resetujemy flagę
        elif line.startswith("Do stosowania:"):
            # Rozpoczęcie sekcji "dane techniczne"
            inside_technical_data = True
            current_product["dane techniczne"]["Do stosowania"] = line.replace("Do stosowania:", "").strip()
        elif inside_technical_data:
            # Jeśli jesteśmy w sekcji "dane techniczne", dodajemy linie do tej sekcji
            property_match = re.match(r"([^:]+):(.*)", line)
            if property_match:
                property_name = property_match.group(1).strip()
                property_value = property_match.group(2).strip()
                current_product["dane techniczne"][property_name] = property_value

# Dodanie ostatniego produktu, jeśli istnieje
if current_product:
    products.append(current_product)

# Zapis do nowego products.json
with open("products_transformed.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=4)

print(f"Przekształcono products.json. Znaleziono {len(products)} produktów.")
