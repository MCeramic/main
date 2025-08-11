# -*- coding: utf-8 -*-
# Updated for Render deployment
# Remove ngrok setup and use static Render URL

import json
import os
import requests
import time
import logging
from flask import Flask, request, send_from_directory, Response
import difflib
from datetime import datetime, timedelta

# Configure logging to file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='a'
)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(console)

# Dictionaries for tracking users and processed events
seen_users = {}
processed_events = {}

# Define tokens (replace with your actual tokens)
PAGE_ACCESS_TOKEN = "EAAI8hsGDfMkBPN1hMM5Glu2OVYpZCw3Qymo5374WYQh7i1vNhaYir7ZCbeojNeetDVxeJ42VgUy30qdLM7Sy8kRO5lM2WCTpNNuByYmyeLWfxcXuLxqKfI7yT11RmhRQiZBGCmGPZBl8ZBcv2zWJsqK4cPZCwZBYMzqQRG3kcrGo1L8L4p3tZBFSM6jQNdTQF4g8agKC"
VERIFY_TOKEN = "mceramic"

app = Flask(__name__)

# Static server URL for Render
SERVER_URL = "https://main-owe4.onrender.com"
logger.info(f"🖧 Using static server URL: {SERVER_URL}")

@app.route('/')
def test():
    logger.info("📡 Otrzymano żądanie na /")
    return "Flask działa!", 200

@app.route('/images/<path:path>')
def serve_image(path):
    logger.info(f"📷 Żądanie obrazu: {path}")
    return send_from_directory('images', path)

@app.route('/robots.txt')
def robots():
    logger.info("📄 robots.txt będzie zwrócony")
    content = """User-agent: *
Allow: /images/
"""
    return Response(content, mimetype='text/plain')

# Systems and products data
page_to_intent_products = {
    2: {"intent": "SYSTEM KLEJENIA ŁAZIENEK Umiarkowane obciążenie wilgocią. Uszczelnienie zespolone", "products": ["ARDEX AM 100", "ARDEX 8+9", "ARDEX SK 12", "ARDEX X 7 G PLUS", "ARDEX G 10 PREMIUM", "ARDEX SE"], "image": "system_lazienkowy_umiarkowane_obciazenie_wilgocia_uszczelnienie_zespolone.png"},
    3: {"intent": "SYSTEM KLEJENIA ŁAZIENEK Umiarkowane obciążenie wilgocią. Mata uszczelniająca", "products": ["ARDEX AM 100", "ARDEX X 7 G PLUS", "ARDEX 7+8", "ARDEX G 10 PREMIUM", "ARDEX SK 12", "ARDEX SK 100 W", "ARDEX SE"], "image": "system_lazienkowy_umiarkowane_obciazenie_wilgocia_mata_uszczelniajaca.png"},
    4: {"intent": "SYSTEM KLEJENIA OKŁADZIN WIELKOFORMATOWYCH Jastrych cementowy wewnątrz pomieszczeń", "products": ["ARDEX P 52", "ARDEX CL 100", "ARDEX COLAFIX 8X8", "ARDEX G 10 PREMIUM", "ARDEX SE"], "image": "okladziny_wielkoformatowe_jastrych_cementowy_wewnatrz_pomieszczen.png"},
    5: {"intent": "SYSTEM KLEJENIA OKŁADZIN WIELKOFORMATOWYCH Jastrych anhydrytowy wewnątrz pomieszczeń", "products": ["ARDEX P 52", "ARDEX S 28 NEU", "ARDEX G 10 PREMIUM", "ARDEX SE"], "image": "okladziny_wielkoformatowe_jastrych_anhydrytowy_wewnatrz_pomieszczen.png"},
    6: {"intent": "SYSTEM KLEJENIA KAMIENIA NATURALNEGO (wrażliwy na wilgoć) Wewnątrz pomieszczeń", "products": ["ARDEX P 52", "ARDEX CL 100", "ARDEX N 23", "ARDEX N 23 W", "ARDEX G 10", "ARDEX C1 100"], "image": "kamien_naturalny_wrazliwy_na_wilgoc_wewnatrz_pomieszczen.png"},
    7: {"intent": "SYSTEM KLEJENIA KAMIENIA NATURALNEGO (niewrażliwy na wilgoć) Wewnątrz pomieszczeń", "products": ["ARDEX P 52", "ARDEX CL 100", "ARDEX X 7 G PLUS", "ARDEX X 7 W PLUS", "ARDEX G 10 PREMIUM", "ARDEX ST"], "image": "kamien_naturalny_niewrazliwy_na_wilgoc_wewnatrz_pomieszczen.png"},
    8: {"intent": "SYSTEM KLEJENIA KAMIENIA NATURALNEGO (niewrażliwy na wilgoć) Na zewnątrz pomieszczeń", "products": ["ARDEX AM 100", "ARDEX 8+9", "ARDEX SK 12", "ARDEX X 32", "ARDEX X 7 G PLUS", "ARDEX G 10 PREMIUM", "ARDEX SE"], "image": "kamien_naturalny_niewrazliwy_na_wilgoc_na_zewnatrz_pomieszczen.png"},
    9: {"intent": "SYSTEM KLEJENIA TARASOWO BALKONOWY Uszczelnienie zespolone", "products": ["ARDEX AM 100", "ARDEX 8+9", "ARDEX SK 12", "ARDEX X 7 G PLUS", "ARDEX G 10 PREMIUM", "ARDEX SE"], "image": "system_tarasowo_balkonowy_uszczelnienie_zespolone.png"},
    10: {"intent": "SYSTEM KLEJENIA BASENÓW", "products": ["ARDEX A 38", "ARDEX AM 100", "ARDEX A 46", "ARDEX S 7 PLUS", "ARDEX SK 12", "ARDEX X 7 G PLUS", "ARDEX X 77 W", "ARDEX RG 12 1-6", "ARDEX G 10 PREMIUM"], "image": "system_basenowy.png"},
    11: {"intent": "SYSTEM KLEJENIA Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Ściana poza prysznicem", "products": ["ARDEX A 45", "ARDEX AF 181 W", "ARDEX SC"], "image": "system_klejenia_dekoracyjnych_wykladzin_lvt_w_pomieszczeniach_mokrych_sciana_poza_prysznicem.png"},
    12: {"intent": "SYSTEM KLEJENIA Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Ściana pod prysznicem", "products": ["ARDEX A 45", "ARDEX FIX", "ARDEX SK 100 W", "ARDEX AF 181 W", "ARDEX SC"], "image": "system_klejenia_dekoracyjnych_wykladzin_lvt_w_pomieszczeniach_mokrych_sciana_pod_prysznicem.png"},
    13: {"intent": "SYSTEM KLEJENIA Dekoracyjnych wykładzin LVT w pomieszczeniach mokrych. Podłoga poza prysznicem", "products": ["ARDEX A 45 FEIN", "ARDEX K 60", "ARDEX SK 100 W", "ARDEX AF 180", "ARDEX AF 181 W", "ARDEX SC"], "image": "system_klejenia_dekoracyjnych_wykladzin_lvt_w_pomieszczeniach_mokrych_podloga_poza_prysznicem.png"},
    14: {"intent": "SYSTEM KLEJENIA Dekoracyjnych wykładzin LVT", "products": ["ARDEX P 4 READY", "ARDEX CL 100", "ARDEX AF 1140", "ARDEX AF 155"], "image": "system_klejenia_dekoracyjnych_wykladzin_lvt.png"},
    15: {"intent": "SYSTEM KLEJENIA Okładzin drewnianych", "products": ["ARDEX A 45 FEIN", "ARDEX PU 30", "ARDEX AF 460", "ARDEX AF 480"], "image": "system_klejenia_okladzin_drewnianych.png"},
    16: {"intent": "SYSTEM KLEJENIA Wykładzin dywanowych", "products": ["ARDEX P 52", "ARDEX CL 100", "ARDEX AF 230"], "image": "system_klejenia_wykladzin_dywanowych.png"}
}

def load_products_data():
    products_data = {}
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            products_list = json.load(f)
            for product in products_list:
                products_data[product["name"]] = product
    except FileNotFoundError:
        logger.warning("⚠️ Plik products.json nie istnieje. Używam domyślnych danych.")
    except json.JSONDecodeError as e:
        logger.error(f"❌ Błąd dekodowania JSON w products.json: {e}")
    return products_data

products_data = load_products_data()

keyword_to_products = {
    "stan surowy": ["ARDEX B 10", "ARDEX B 12", "ARDEX B 14", "ARDEX B 16", "ARDEX HUMISTOP GREY", "ARDEX HUMISTOP FLEX", "ARDEX AM 100", "ARDEX A 38", "ARDEX A 38 MIX", "ARDEX A 58", "ARDEX A 18", "ARDEX QS", "ARDEX E 100", "ARDEX BM", "ARDEX BM-P", "ARDEX BM-T10"],
    "jastrych": ["ARDEX B 10", "ARDEX B 12", "ARDEX B 14", "ARDEX B 16", "ARDEX HUMISTOP GREY", "ARDEX HUMISTOP FLEX", "ARDEX AM 100", "ARDEX A 38", "ARDEX A 38 MIX", "ARDEX A 58", "ARDEX A 18", "ARDEX QS", "ARDEX E 100", "ARDEX BM", "ARDEX BM-P", "ARDEX BM-T10"],
    "gruntowanie": ["ARDEX EP 2000", "ARDEX EP 2001", "ARDEX FB", "ARDEX PU 5", "ARDEX P 52", "ARDEX P 4 READY", "ARDEX P 82", "ARDEX PU 30"],
    "wyrównanie posadzki": ["ARDEX CL 50", "ARDEX CL 100", "ARDEX CL 300", "ARDEX K 36 NEU", "ARDEX K 80", "ARDEX K 301", "ARDEX A 45 FEIN", "ARDEX A 46"],
    "powłoki posadzkowe": ["ARDEX R 2 E", "ARDEX R 50 ES"],
    "uszczelnienia podtynkowe": ["ARDEX S 1-K", "ARDEX S 7 PLUS", "ARDEX S 8 FLOW", "ARDEX 8+9", "ARDEX EP 500", "ARDEX S 2-K PU", "ARDEX 7+8", "ARDEX SK 100 W", "ARDEX SK TRICOM", "ARDEX SK 12 TRICOM", "ARDEX SK 12 BT TRICOM", "ARDEX S 2-K C", "ARDEX SK 4 PROTECT", "ARDEX PT 120"],
    "klejenie płytek i kamienia": ["ARDEX X 7 G PLUS", "ARDEX X 7 G S", "ARDEX X 7 W", "ARDEX X 77", "ARDEX X 77 S", "ARDEX X 77 W", "ARDEX X 78", "ARDEX X 78 S", "ARDEX X 80", "ARDEX S 28 NEU", "ARDEX N 23", "ARDEX N 23 W", "ARDEX X 32", "ARDEX WA (klej)", "ARDEX E 90"],
    "fugowanie": ["ARDEX RG 12 1-6", "ARDEX RG CLEANER", "ARDEX WA (fuga)", "ARDEX CA 20 P", "ARDEX SE", "ARDEX ST", "ARDEX SC MATT", "ARDEX SG"],
    "klejenie podłóg": ["ARDEX AF 2224", "ARDEX AF 2270", "ARDEX AF 823", "ARDEX AF 130", "ARDEX AF 140", "ARDEX AF 155", "ARDEX AF 180", "ARDEX AF 181 W", "ARDEX AF 185", "ARDEX AF 785", "ARDEX AF 230", "ARDEX AF 270", "ARDEX AF 290", "ARDEX AF 460", "ARDEX AF 480", "ARDEX AF 490 - Klej 2K-PU do parkietu", "ARDEX AF 495", "ARDEX AF 660", "ARDEX AF 800", "ARDEX AF 825", "ARDEX AF 824", "ARDEX CW"],
    "szpachlowanie ścian": ["ARDEX A 828", "ARDEX A 828 COMFORT", "ARDEX W 820 SUPERFINISH", "ARDEX RF (w kartuszu)"],
    "naprawa konstrukcji i powierzchni": ["ARDEX AM 100", "ARDEX B 10", "ARDEX B 12", "ARDEX B 14", "ARDEX B 16", "ARDEX CEM GROUT", "ARDEX HUMISTOP", "ARDEX A 45 FEIN", "ARDEX A 46", "ARDEX F 11"],
    "naprawa pęknięć": ["ARDEX EP 2000", "ARDEX PU 5"],
    "posadzki epoksydowe": ["ARDEX R 50 ES", "ARDEX R 2 E", "ARDEX QS"],
    "naprawa podłoża": ["ARDEX PU 5"],
    "odcięcie wilgotności": ["ARDEX EP 2000"],
    "masy rozlewne do wyrównania posadzki": ["ARDEX CL 50", "ARDEX CL 100", "ARDEX CL 300", "ARDEX K 60"],
    "masy szpachlowe do wyrównania posadzki": ["ARDEX A 45 FEIN"],
    "kleje uniwersalne": ["ARDEX AF 2224", "ARDEX AF 2270"],
    "kleje do wykładzin tekstylnych": ["ARDEX AF 230", "ARDEX AF 270", "ARDEX AF 290"],
    "kleje do wykładzin elastycznych": ["ARDEX AF 130", "ARDEX AF 140", "ARDEX AF 155", "ARDEX AF 180", "ARDEX AF 181 W"],
    "klej do linoleum i korka": ["ARDEX AF 785"],
    "środek mocujący do płytek wykładzinowych": ["ARDEX AF 825", "ARDEX AF 824"],
    "klej kontaktowy": ["ARDEX AF 635", "ARDEX AF 660"],
    "środki czyszczące": ["ARDEX CW", "ARDEX RG CLEANER"],
    "system uszczelnień": ["ARDEX AK 100", "ARDEX SK 12 TRICOM", "ARDEX SK TRICOM"],
    "gruntowanie chłonne podłoża (beton, jastrych, tynk, gips)": ["ARDEX P 52"],
    "gruntowanie nie chłonne podłoża (płytki, lamperie, metal, szkło)": ["ARDEX P 4 READY", "ARDEX P 82"],
    "gruntowanie lastriko": ["ARDEX EP 2000", "ARDEX QS"],
    "reprofilacja (ściana, podłoga) masy gęstoplastyczne wewnątrz": ["ARDEX A 45 FEIN", "ARDEX A 46", "ARDEX M 4", "ARDEX AM 100"],
    "reprofilacja (ściana, podłoga) masy gęstoplastyczne zewnątrz": ["ARDEX A 46", "ARDEX M 4", "ARDEX AM 100"],
    "reprofilacja (podłoga) masy rozlewne wewnątrz": ["ARDEX CL 100", "ARDEX K 14", "ARDEX K 80"],
    "reprofilacja (podłoga) masy rozlewne zewnątrz": ["ARDEX K 301"],
    "izolację podpłytkowe wewnątrz": ["ARDEX S 1-K", "ARDEX 8+9"],
    "izolację podpłytkowe Zewnątrz": ["ARDEX 8+9", "ARDEX S 7 PLUS"],
    "okładziny drewniane": ["ARDEX A 45 FEIN", "ARDEX PU 30", "ARDEX AF 460", "ARDEX AF 480"],
    "płyty wielkoformatowe": ["ARDEX COLAFIX 8X8"]
}

# Utility function to split long messages
def split_message(text, max_length=1900):
    if len(text) <= max_length:
        return [text]
    messages = []
    current_message = ""
    for line in text.split("\n"):
        if len(current_message) + len(line) + 1 > max_length:
            messages.append(current_message.strip())
            current_message = line
        else:
            current_message += "\n" + line if current_message else line
    if current_message:
        messages.append(current_message.strip())
    return messages

def _normalize_name(s):
    """Usuń spacje i znaki specjalne, zamień na lowercase."""
    return "".join(ch.lower() for ch in s if ch.isalnum())


def search_products(sender_id, user_text, return_products_only=False):
    import difflib

    user_text_orig = user_text
    user_text = user_text.lower().strip()
    if user_text.startswith("⚠️"):
        logger.debug(f"Skipped processing error message: {user_text}")
        return None

    matching_products = set()
    u_norm = _normalize_name(user_text)

    # --- Dopasowanie po nazwach produktów (direct / substring / fuzzy) ---
    all_products = set()
    for p_list in keyword_to_products.values():
        all_products.update(p_list)
    for sys in page_to_intent_products.values():
        all_products.update(sys.get("products", []))

    for prod in all_products:
        p_norm = _normalize_name(prod)
        if not u_norm:
            continue
        if u_norm == p_norm or u_norm in p_norm or p_norm in u_norm:
            matching_products.add(prod)
            logger.debug(f"Produkt dopasowany (name match): '{prod}' <- '{user_text_orig}'")
            continue
        score = difflib.SequenceMatcher(None, u_norm, p_norm).ratio()
        if score > 0.75:
            matching_products.add(prod)
            logger.debug(f"Produkt dopasowany fuzzy ({score:.2f}): '{prod}' <- '{user_text_orig}'")

    # --- Dopasowanie po keywordach ---
    for keyword, products in keyword_to_products.items():
        keyword_lower = keyword.lower()
        match_ratio = difflib.SequenceMatcher(None, user_text, keyword_lower).ratio()
        if match_ratio > 0.4 or user_text in keyword_lower:
            matching_products.update(products)
            logger.debug(f"Dopasowano keyword '{keyword}' z ratio {match_ratio:.2f}")

    # --- Dopasowanie po nazwach systemów (intent) ---
    for page_num, system_data in page_to_intent_products.items():
        intent = system_data["intent"].lower()
        system_products = system_data.get("products", [])
        match_ratio = difflib.SequenceMatcher(None, user_text, intent).ratio()
        if match_ratio > 0.4 or user_text in intent:
            matching_products.update(system_products)
            logger.debug(f"Dopasowano system '{intent}' z ratio {match_ratio:.2f}")

    matching_products = sorted(list(matching_products))

    if matching_products:
        logger.info(f"🛠️ Znaleziono {len(matching_products)} pasujących produktów dla '{user_text}'")
        if return_products_only:
            return matching_products
        product_list = "\n".join([f"• {product}" for product in matching_products[:15]])
        initial_message = f"🛠️ Znalazłem pasujące produkty:\n{product_list}\n\nCo chcesz zobaczyć?"
        buttons = [
            {"type": "postback", "title": "Opis produktu", "payload": f"DESCRIBE_PRODUCT_{user_text}"},
            {"type": "postback", "title": "Systemy", "payload": f"SHOW_SYSTEMS_{user_text}"}
        ]
        return [{
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": initial_message,
                    "buttons": buttons
                }
            }
        }]

    logger.warning(f"⚠️ Nie znaleziono pasujących produktów dla '{user_text}'")
    return [{"text": "⚠️ Nie znalazłem pasujących produktów. Spróbuj inaczej!"}]


def search_systems(sender_id, user_text):
    import difflib

    user_text_lower = user_text.lower().strip()
    if user_text_lower.startswith("⚠️"):
        logger.debug(f"Skipped processing error message: {user_text_lower}")
        return None

    found_products = search_products(sender_id, user_text, return_products_only=True)
    matching_systems = []

    # 1️⃣ Szukanie po produktach
    if found_products:
        normalized_found_products = {_normalize_name(p) for p in found_products}
        for page_num, system_data in page_to_intent_products.items():
            normalized_system_products = {_normalize_name(p) for p in system_data.get("products", [])}
            common_products = normalized_found_products & normalized_system_products
            if common_products:
                matching_systems.append((page_num, system_data["intent"], len(common_products)))

    # 2️⃣ Fallback — dopasowanie po nazwie systemu (intent)
    if not matching_systems:
        normalized_user = _normalize_name(user_text_lower)
        for page_num, system_data in page_to_intent_products.items():
            intent_norm = _normalize_name(system_data["intent"])
            ratio = difflib.SequenceMatcher(None, normalized_user, intent_norm).ratio()
            if ratio > 0.5 or normalized_user in intent_norm:
                matching_systems.append((page_num, system_data["intent"], int(ratio * 100)))

    # 3️⃣ Wyniki
    if matching_systems:
        matching_systems.sort(key=lambda x: x[2], reverse=True)
        system_list = "\n".join([f"{i+1}. {system[1]}" for i, system in enumerate(matching_systems[:3])])
        initial_message = f"🔍 Znaleziono pasujące systemy:\n{system_list}"
        buttons = [
            {"type": "postback", "title": f"System {i+1}", "payload": f"SELECT_SYSTEM_{system[0]}"}
            for i, system in enumerate(matching_systems[:3])
        ]
        logger.info(f"🔍 Znaleziono {len(matching_systems)} pasujących systemów dla '{user_text}'")
        return [
            {"text": initial_message},
            {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": "📋 Wybierz system:",
                        "buttons": buttons
                    }
                }
            }
        ]

    logger.warning(f"⚠️ Nie znaleziono systemów pasujących do zapytania '{user_text}'")
    return [{"text": "⚠️ Nie znalazłem systemów pasujących do zapytania."}]

def describe_product(sender_id, user_text):
    user_text = user_text.lower()
    logger.debug(f"📋 Rozpoczynam describe_product dla '{user_text}'")
    
    user_keywords = set(user_text.split())
    best_match = None
    best_score = 0
    
    for keyword, products in keyword_to_products.items():
        keyword_lower = keyword.lower()
        keyword_words = set(keyword_lower.split())
        common_keywords = user_keywords.intersection(keyword_words)
        match_ratio = difflib.SequenceMatcher(None, user_text, keyword_lower).ratio()
        
        score = len(common_keywords) * 2 + match_ratio
        if score > best_score and (len(common_keywords) > 0 or match_ratio > 0.5):
            best_score = score
            best_match = products
    
    if best_match:
        initial_products = best_match[:2]
        buttons = [{"type": "postback", "title": product[:20], "payload": f"SHOW_PRODUCT_{product}"} for product in initial_products]
        if len(best_match) > 2:
            buttons.append({"type": "postback", "title": "Inne produkty", "payload": f"MORE_PRODUCTS_{user_text}_2"})
        logger.info(f"📋 Przygotowuję wybór produktów dla '{user_text}' z {len(buttons)} przyciskami, wynik: {best_score}")
        return [{"attachment": {"type": "template", "payload": {"template_type": "button", "text": "📋 Wybierz produkt, aby zobaczyć opis i dane techniczne:", "buttons": buttons}}}]
    
    logger.warning(f"⚠️ Brak produktów do opisania dla '{user_text}'")
    return [{"text": "⚠️ Brak produktów do opisania."}]

def show_more_products(sender_id, payload):
    logger.debug(f"📋 Rozpoczynam show_more_products dla payloadu: '{payload}'")
    parts = payload.split("_")
    logger.debug(f"Rozdzielony payload: {parts}, liczba części: {len(parts)}")
    
    if len(parts) > 3 and parts[0] == "MORE" and parts[1] == "PRODUCTS":
        parts = ["MORE_PRODUCTS"] + parts[2:]
        logger.debug(f"Skorygowany payload: {parts}, nowa liczba części: {len(parts)}")
    
    if len(parts) != 3 or parts[0] != "MORE_PRODUCTS":
        logger.error(f"❌ Nieprawidłowy format payloadu: {payload}")
        return [{"text": "⚠️ Wystąpił błąd. Spróbuj ponownie."}]
    
    user_text = parts[1].lower()
    logger.debug(f"User_text: {user_text}")
    try:
        start_index = int(parts[2])
        logger.debug(f"Start_index: {start_index}")
    except ValueError:
        logger.error(f"❌ Nieprawidłowy start_index w payloadzie: {payload}")
        return [{"text": "⚠️ Wystąpił błąd. Spróbuj ponownie."}]

    user_keywords = set(user_text.split())
    best_match = None
    best_score = 0
    
    for keyword, products in keyword_to_products.items():
        keyword_lower = keyword.lower()
        keyword_words = set(keyword_lower.split())
        common_keywords = user_keywords.intersection(keyword_words)
        match_ratio = difflib.SequenceMatcher(None, user_text, keyword_lower).ratio()
        
        score = len(common_keywords) * 2 + match_ratio
        if score > best_score and (len(common_keywords) > 0 or match_ratio > 0.5):
            best_score = score
            best_match = products
    
    if best_match and len(best_match) > start_index:
        remaining_products = best_match[start_index:]
        next_products = remaining_products[:2]
        messages = []
        response_text = "🛠️ Pozostałe produkty:\n" + "\n".join(
            [f"• {p}: {products_data.get(p, {}).get('description', 'Szczegóły na ardex.pl')}" for p in next_products]
        )
        messages.extend(split_message(response_text))
        buttons = [{"type": "postback", "title": p[:20], "payload": f"SHOW_PRODUCT_{p}"} for p in next_products]
        if len(remaining_products) > 2:
            next_index = start_index + 2
            buttons.append({"type": "postback", "title": "Inne produkty", "payload": f"MORE_PRODUCTS_{user_text}_{next_index}"})
        messages.append({"attachment": {"type": "template", "payload": {"template_type": "button", "text": "📋 Wybierz kolejny produkt:", "buttons": buttons}}})
        logger.info(f"📋 Wysłano kolejne produkty dla '{user_text}' od indeksu {start_index} z wynikiem {best_score}")
        return messages
    
    logger.info(f"ℹ️ Brak dodatkowych produktów dla '{user_text}' od indeksu {start_index}")
    return [{"text": "ℹ️ Nie ma więcej produktów do pokazania."}]

def show_product_details(sender_id, payload):
    logger.debug(f"📋 Rozpoczynam show_product_details dla '{payload}'")
    
    if payload.startswith("SHOW_PRODUCT_DESCRIPTIONS_"):
        try:
            system_id = int(payload.replace("SHOW_PRODUCT_DESCRIPTIONS_", ""))
            system_data = page_to_intent_products.get(system_id)
            
            if not system_data or "products" not in system_data:
                logger.warning(f"⚠️ Nie znaleziono systemu o ID {system_id}")
                send_message(sender_id, {"text": f"⚠️ Nie znaleziono systemu {system_id}. Szczegóły na ardex.pl"})
                return
            
            products = system_data["products"]
            response = f"Opisy produktów dla {system_data['intent']}:\n\n"
            
            for product_name in products:
                product_data = products_data.get(product_name)
                if product_data:
                    response += f"**{product_name}**: {product_data['description']}\n\n"
                else:
                    response += f"**{product_name}**: Szczegóły na ardex.pl\n\n"
            
            for msg in split_message(response.strip()):
                send_message(sender_id, {"text": msg})
        
        except ValueError:
            logger.warning(f"⚠️ Nieprawidłowy format payloadu: {payload}")
            send_message(sender_id, {"text": "⚠️ Błąd przetwarzania żądania. Spróbuj ponownie."})
    elif payload.startswith("SHOW_PRODUCT_"):
        product_name = payload.replace("SHOW_PRODUCT_", "")
        product_data = products_data.get(product_name)
        if product_data:
            response = f"**{product_name}**\n📝 Opis: {product_data['description']}"
            dane_techniczne = product_data.get("dane techniczne", {})
            if dane_techniczne:
                response += "\n🔧 Dane techniczne:" + "\n".join([f"\n  • {key}: {value}" for key, value in dane_techniczne.items()])
            else:
                response += "\n🔧 Brak danych technicznych."
            for msg in split_message(response, max_length=640):
                send_message(sender_id, {"text": msg})
        else:
            send_message(sender_id, {"text": f"⚠️ Brak danych dla {product_name}. Szczegóły na ardex.pl"})
    else:
        logger.warning(f"⚠️ Nieobsługiwany payload: {payload}")
        send_message(sender_id, {"text": f"⚠️ Brak danych dla {payload}. Szczegóły na ardex.pl"})

def describe_system(sender_id, page_num):
    if page_num not in page_to_intent_products:
        logger.warning(f"⚠️ System {page_num} nie istnieje")
        return [{"text": "⚠️ Wybrany system nie istnieje."}]
    system = page_to_intent_products[page_num]
    intent_name = system["intent"]
    image_filename = system["image"]
    messages = [{"text": f"📋 Wybrany system: {intent_name}"}]
    image_path = os.path.join("images", image_filename)
    if os.path.exists(image_path):
        image_url = f"{SERVER_URL}/images/{image_filename}"
        logger.debug(f"📷 Przygotowano URL obrazu: {image_url}")
        messages.append({"attachment": {"type": "image", "payload": {"url": image_url, "is_reusable": True}}})
    else:
        logger.warning(f"⚠️ Obraz {image_path} nie istnieje, pomijam wysyłanie")
        messages.append({"text": f"ℹ️ Obraz dla systemu '{intent_name}' nie jest dostępny."})
    buttons = [
        {"type": "postback", "title": "1. Opis produktów", "payload": f"SHOW_PRODUCT_DESCRIPTIONS_{page_num}"},
        {"type": "postback", "title": "2. Dane techniczne", "payload": f"SHOW_PRODUCT_TECH_DATA_{page_num}"}
    ]
    messages.append({"attachment": {"type": "template", "payload": {"template_type": "button", "text": "📋 Co chcesz zobaczyć?", "buttons": buttons}}})
    logger.info(f"✅ Wysłano system {page_num} z {len(messages)} wiadomościami")
    return messages

def show_product_tech_data(sender_id, page_num):
    if page_num not in page_to_intent_products:
        logger.warning(f"⚠️ System {page_num} nie istnieje")
        return [{"text": "⚠️ Wybrany system nie istnieje."}]
    system = page_to_intent_products[page_num]
    intent_name = system["intent"]
    products_list = system["products"]
    messages = [{"text": f"📋 Dane techniczne produktów z systemu: {intent_name}"}]
    
    # Tworzymy słownik produktów z products_data z normalizacją kluczy (bez spacji, lowercase)
    normalized_products_data = {k.replace(" ", "").lower(): v for k, v in products_data.items()}
    
    for product_name in products_list:
        # Normalizujemy nazwę produktu do porównania
        normalized_product_name = product_name.replace(" ", "").lower()
        product_info = normalized_products_data.get(normalized_product_name, {})
        dane_techniczne = product_info.get("dane techniczne", {})
        
        if dane_techniczne:
            product_text = f"🛠️ {product_name}\n🔧 Dane techniczne:" + "\n".join([f"\n  • {key}: {value}" for key, value in dane_techniczne.items()])
        else:
            product_text = f"🛠️ {product_name}\n🔧 Brak danych technicznych."
        messages.extend([{"text": msg} for msg in split_message(product_text, max_length=640)])
    
    logger.info(f"✅ Wysłano dane techniczne produktów z systemu {page_num} z {len(messages)} wiadomościami")
    return messages

def send_message(recipient_id, message):
    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    # Dla obrazów - wysyłaj bezpośrednio URL (bez uploadu)
    if "attachment" in message and message["attachment"]["type"] == "image":
        image_url = message["attachment"]["payload"].get("url")
        if image_url and not image_url.startswith("http"):
            image_url = f"{SERVER_URL}/{image_url}"
        
        # Aktualizuj URL w wiadomości
        message["attachment"]["payload"]["url"] = image_url
        # Usuń is_reusable - może powodować problemy
        message["attachment"]["payload"].pop("is_reusable", None)
        
        logger.info(f"📷 Wysyłam obraz bezpośrednio: {image_url}")
    
    payload = {"recipient": {"id": recipient_id}, "message": message, "messaging_type": "RESPONSE"}
    logger.debug(f"Wysyłam payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json; charset=utf-8"})
        response.raise_for_status()
        logger.info(f"✅ Wiadomość wysłana: {json.dumps(message, ensure_ascii=False)}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Błąd wysyłania: {getattr(response, 'status_code', 'brak kodu')}")
        logger.error(f"❌ Response: {getattr(response, 'text', str(e))}")
        
        # Fallback - wyślij jako link tekstowy jeśli obraz się nie uda
        if "attachment" in message and message["attachment"]["type"] == "image":
            fallback_url = message["attachment"]["payload"]["url"]
            fallback_message = {"text": f"📷 Schemat systemu: {fallback_url}"}
            logger.info("📷 Używam fallback - wysyłam jako link tekstowy")
            return send_message(recipient_id, fallback_message)
        return False

def describe_system(sender_id, page_num):
    if page_num not in page_to_intent_products:
        logger.warning(f"⚠️ System {page_num} nie istnieje")
        return [{"text": "⚠️ Wybrany system nie istnieje."}]
    
    system = page_to_intent_products[page_num]
    intent_name = system["intent"]
    image_filename = system["image"]
    
    messages = [{"text": f"📋 Wybrany system: {intent_name}"}]
    
    # Sprawdź czy obraz istnieje lokalnie
    image_path = os.path.join("images", image_filename)
    if os.path.exists(image_path):
        image_url = f"{SERVER_URL}/images/{image_filename}"
        logger.debug(f"📷 Przygotowano URL obrazu: {image_url}")
        
        # Dodaj wiadomość z obrazem (bez is_reusable)
        messages.append({
            "attachment": {
                "type": "image",
                "payload": {
                    "url": image_url
                }
            }
        })
    else:
        logger.warning(f"⚠️ Obraz {image_path} nie istnieje")
        messages.append({"text": f"ℹ️ Schemat dla systemu '{intent_name}' będzie dostępny wkrótce."})
    
    # Dodaj przyciski
    buttons = [
        {"type": "postback", "title": "1. Opis produktów", "payload": f"SHOW_PRODUCT_DESCRIPTIONS_{page_num}"},
        {"type": "postback", "title": "2. Dane techniczne", "payload": f"SHOW_PRODUCT_TECH_DATA_{page_num}"}
    ]
    messages.append({
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "button",
                "text": "📋 Co chcesz zobaczyć?",
                "buttons": buttons
            }
        }
    })
    
    logger.info(f"✅ Przygotowano system {page_num} z {len(messages)} wiadomościami")
    return messages
    
# Add this function to debug your data structures
def debug_data_structures():
    """Debug function to check data structure contents"""
    logger.info("=== DEBUGGING DATA STRUCTURES ===")
    
    logger.info(f"page_to_intent_products keys: {list(page_to_intent_products.keys())}")
    
    for page_num, system_data in list(page_to_intent_products.items())[:3]:  # First 3 systems
        logger.info(f"System {page_num}:")
        logger.info(f"  Intent: {system_data.get('intent', 'N/A')}")
        logger.info(f"  Products: {system_data.get('products', [])}")
    
    logger.info(f"keyword_to_products keys: {list(keyword_to_products.keys())[:5]}")  # First 5 keywords
    
    for keyword, products in list(keyword_to_products.items())[:2]:  # First 2 keywords
        logger.info(f"Keyword '{keyword}' -> Products: {products}")
    
    logger.info(f"products_data keys: {list(products_data.keys())[:10]}")  # First 10 products
    
    logger.info("=== END DEBUG ===")

def cleanup_old_users():
    now = datetime.now()
    cutoff_time = now - timedelta(days=30)
    old_users = [user_id for user_id, timestamp in seen_users.items() if timestamp < cutoff_time]
    for user_id in old_users:
        del seen_users[user_id]
        if user_id in processed_events:
            del processed_events[user_id]
    logger.info(f"🧹 Wyczyszczono {len(old_users)} starych użytkowników. Aktualna liczba: {len(seen_users)}")
    
@app.route('/test-images')
def test_images():
    results = []
    for page_num, system_data in page_to_intent_products.items():
        image_filename = system_data["image"]
        image_path = os.path.join("images", image_filename)
        image_url = f"{SERVER_URL}/images/{image_filename}"
        
        exists_locally = os.path.exists(image_path)
        
        # Test HTTP dostępności
        try:
            response = requests.head(image_url, timeout=5)
            http_available = response.status_code == 200
        except:
            http_available = False
        
        results.append({
            "page": page_num,
            "filename": image_filename,
            "local_exists": exists_locally,
            "http_available": http_available,
            "url": image_url
        })
    
    return {"images": results}

# Dodaj też prosty test pojedynczego obrazu
@app.route('/test-single-image')
def test_single_image():
    # Test pierwszego dostępnego obrazu
    test_image = "system_lazienkowy_umiarkowane_obciazenie_wilgocia_uszczelnienie_zespolone.png"
    image_url = f"{SERVER_URL}/images/{test_image}"
    
    return f'''
    <h2>Test obrazu:</h2>
    <p>URL: {image_url}</p>
    <img src="{image_url}" style="max-width: 500px;" onerror="this.style.display='none'; this.nextSibling.style.display='block';">
    <p style="display:none; color:red;">❌ Obraz nie może być załadowany</p>
    '''

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get("object") != "page":
        logger.debug("📩 [Webhook] Brak danych lub nie jest to strona")
        return "OK", 200

    logger.debug(f"📩 [Webhook] Otrzymano dane: {json.dumps(data, indent=2, ensure_ascii=False)}")

    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            sender_id = messaging_event["sender"]["id"]
            timestamp = messaging_event.get("timestamp", 0)
            event_id = f"{sender_id}_{timestamp}"

            # Ignoruj echo bota
            if "message" in messaging_event and messaging_event["message"].get("is_echo"):
                logger.debug(f"📣 Ignoruję echo bota: {event_id}")
                continue

            # Sprawdzanie duplikatów
            if sender_id not in processed_events:
                processed_events[sender_id] = set()
            if event_id in processed_events[sender_id]:
                logger.info(f"📣 [Webhook] Ignoruję duplikat: {event_id}")
                continue
            processed_events[sender_id].add(event_id)

            logger.info(f"👤 [Webhook] Sender ID: {sender_id}")

            # Powitanie nowych użytkowników
            if sender_id not in seen_users:
                welcome_message = {"text": "👋 Cześć! Jestem botem ARDEX. Wpisz, czego szukasz."}
                send_message(sender_id, welcome_message)
            seen_users[sender_id] = datetime.now()

            # Obsługa wiadomości tekstowych
            if "message" in messaging_event and "text" in messaging_event["message"]:
                user_text = messaging_event["message"]["text"]
                logger.info(f"📨 [Webhook] Wiadomość: {user_text}")
                send_message(sender_id, {"text": "🔍 Szukam dla Ciebie..."})

                product_messages = search_products(sender_id, user_text)
                for message in product_messages:
                    send_message(sender_id, message)

            # Obsługa postbacków
            elif "postback" in messaging_event:
                payload = messaging_event["postback"]["payload"]
                logger.info(f"📩 [Webhook] Postback: {payload}")

                if payload.startswith("DESCRIBE_PRODUCT_"):
                    product_id = payload.replace("DESCRIBE_PRODUCT_", "")
                    messages = describe_product(sender_id, product_id)
                    for message in messages:
                        send_message(sender_id, message)

                elif payload.startswith("MORE_PRODUCTS_") or payload.startswith("SHOW_MORE_PRODUCTS_"):
                    normalized_payload = payload.replace("SHOW_MORE_PRODUCTS_", "MORE_PRODUCTS_")
                    messages = show_more_products(sender_id, normalized_payload)
                    for message in messages:
                        send_message(sender_id, message)

                elif payload.startswith("SHOW_PRODUCT_") or payload.startswith("SHOW_PRODUCT_DESCRIPTIONS_") or payload.startswith("SHOW_PRODUCT_TECH_DATA_"):
                    show_product_details(sender_id, payload)

                elif payload == "SHOW_SYSTEMS":
                    buttons = []
                    for page_num, system_data in page_to_intent_products.items():
                        title = system_data.get("intent", f"System {page_num}")
                        buttons.append({
                            "type": "postback",
                            "title": title[:20],
                            "payload": f"SELECT_SYSTEM_{page_num}"
                        })
                        if len(buttons) >= 10:
                            break
                    if buttons:
                        message = {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "button",
                                    "text": "📋 Wybierz system:",
                                    "buttons": buttons
                                }
                            }
                        }
                        send_message(sender_id, message)
                    else:
                        send_message(sender_id, {"text": "⚠️ Brak dostępnych systemów."})

                elif payload.startswith("SELECT_SYSTEM_"):
                    try:
                        page_num = int(payload.replace("SELECT_SYSTEM_", ""))
                        messages = describe_system(sender_id, page_num)
                        for message in messages:
                            send_message(sender_id, message)
                    except ValueError:
                        send_message(sender_id, {"text": "⚠️ Nieprawidłowy identyfikator systemu."})

                elif payload.startswith("SHOW_PRODUCT_TECH_DATA_"):
                    page_num = int(payload.replace("SHOW_PRODUCT_TECH_DATA_", ""))
                    messages = show_product_tech_data(sender_id, page_num)
                    for message in messages:
                        send_message(sender_id, message)

                elif payload.startswith("SHOW_PRODUCTS_"):
                    user_text = payload.replace("SHOW_PRODUCTS_", "")
                    product_messages = search_products(sender_id, user_text)
                    if product_messages:
                        for message in product_messages:
                            send_message(sender_id, message)
                    else:
                        send_message(sender_id, {"text": "⚠️ Nie znalazłem produktów pasujących do tego zapytania. Spróbuj inaczej!"})

                else:
                    logger.warning(f"Nieobsługiwany payload postbacku: {payload}")
                    send_message(sender_id, {"text": f"⚠️ Nieznany postback: {payload}"})

    cleanup_old_users()
    return "OK", 200

# Endpoint do weryfikacji webhooka Facebooka
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        logger.info("✔️ Weryfikacja webhooka powiodła się")
        return request.args.get("hub.challenge"), 200
    logger.warning("❌ Weryfikacja webhooka nie powiodła się")
    return "Verification failed", 403

if __name__ == "__main__":
    os.makedirs("images", exist_ok=True)
    port_env = os.environ.get("PORT")
    if not port_env:
        logger.error("🛑 Nie znaleziono zmiennej środowiskowej PORT")
        exit(1)
    port = int(port_env)
    logger.info(f"🚀 Uruchamiam Flask na porcie {port}")
    app.run(host="0.0.0.0", port=port, debug=False)






