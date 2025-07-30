# -*- coding: utf-8 -*-
# Updated for Render deployment
# Fixed Facebook media server access issues

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

# Define tokens (get from environment variables with fallbacks)
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "EAAI8hsGDfMkBPN1hMM5Glu2OVYpZCw3Qymo5374WYQh7i1vNhaYir7ZCbeojNeetDVxeJ42VgUy30qdLM7Sy8kRO5lM2WCTpNNuByYmyeLWfxcXuLxqKfI7yT11RmhRQiZBGCmGPZBl8ZBcv2zWJsqK4cPZCwZBYMzqQRG3kcrGo1L8L4p3tZBFSM6jQNdTQF4g8agKC")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mceramic")

app = Flask(__name__)

# Static server URL for Render
SERVER_URL = os.getenv("SERVER_URL", "https://main-owe4.onrender.com")
logger.info(f"🖧 Using server URL: {SERVER_URL}")

@app.route('/')
def test():
    logger.info("📡 Otrzymano żądanie na /")
    return "Flask działa!", 200

@app.route('/images/<path:path>')
def serve_image(path):
    logger.info(f"📷 Żądanie obrazu: {path}")
    
    # Check if file exists first
    import os
    file_path = os.path.join('images', path)
    
    if os.path.exists(file_path):
        try:
            # Add proper headers for Facebook's media server
            response = send_from_directory('images', path)
            
            # Set proper MIME type based on file extension
            if path.lower().endswith('.png'):
                response.headers['Content-Type'] = 'image/png'
            elif path.lower().endswith('.jpg') or path.lower().endswith('.jpeg'):
                response.headers['Content-Type'] = 'image/jpeg'
            elif path.lower().endswith('.gif'):
                response.headers['Content-Type'] = 'image/gif'
            elif path.lower().endswith('.webp'):
                response.headers['Content-Type'] = 'image/webp'
            elif path.lower().endswith('.svg'):
                response.headers['Content-Type'] = 'image/svg+xml'
            
            # Enhanced headers specifically for Facebook's media crawler
            response.headers['Cache-Control'] = 'public, max-age=86400'  # 24 hours
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'User-Agent, Content-Type'
            
            # Facebook-specific headers
            response.headers['X-Robots-Tag'] = 'noindex, nofollow'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            logger.info(f"✅ Obraz {path} zwrócony z nagłówkami Facebook-friendly")
            return response
            
        except Exception as e:
            logger.error(f"❌ Błąd podczas zwracania obrazu {path}: {e}")
    
    # Return a placeholder SVG image instead of 404
    logger.warning(f"⚠️ Obraz nie znaleziony: {path}")
    placeholder_svg = f'''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
        <rect width="400" height="300" fill="#f8f9fa" stroke="#dee2e6"/>
        <text x="200" y="140" text-anchor="middle" font-family="Arial" font-size="14" fill="#6c757d">
            ARDEX Product Image
        </text>
        <text x="200" y="160" text-anchor="middle" font-family="Arial" font-size="12" fill="#adb5bd">
            {path}
        </text>
        <text x="200" y="180" text-anchor="middle" font-family="Arial" font-size="10" fill="#ced4da">
            Image placeholder - coming soon
        </text>
    </svg>'''
    
    response = Response(placeholder_svg, mimetype='image/svg+xml')
    response.headers['Cache-Control'] = 'public, max-age=3600'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response

@app.route('/robots.txt')
def robots():
    logger.info("📄 robots.txt będzie zwrócony")
    # Updated robots.txt to specifically allow Facebook's media crawlers
    content = """User-agent: *
Allow: /images/

User-agent: facebookexternalhit
Allow: /

User-agent: facebookexternalhit/1.1
Allow: /

User-agent: Facebot
Allow: /

User-agent: FacebookBot
Allow: /

User-agent: Meta-ExternalAgent
Allow: /

User-agent: Meta-ExternalFetcher
Allow: /

User-agent: WhatsApp
Allow: /

Sitemap: """ + SERVER_URL + """/sitemap.xml
"""
    return Response(content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    """Generate a basic sitemap for better crawling"""
    logger.info("📄 sitemap.xml będzie zwrócony")
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{SERVER_URL}/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{SERVER_URL}/images/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""
    return Response(sitemap_content, mimetype='application/xml')

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

# Improved system search with better filtering
def search_systems(sender_id, user_text):
    user_text = user_text.lower()
    if user_text.startswith("⚠️"):
        logger.debug(f"Skipped processing error message: {user_text}")
        return None
    
    # Pobieramy listę wcześniej znalezionych produktów
    found_products = search_products(sender_id, user_text, return_products_only=True)
    if not found_products:
        logger.warning(f"⚠️ Nie znaleziono produktów dla '{user_text}', więc brak systemów")
        return None
    
    # Szukamy systemów zawierających te produkty
    matching_systems = []
    for page_num, system_data in page_to_intent_products.items():
        system_intent = system_data["intent"].lower()
        system_products = system_data.get("products", [])
        # Sprawdzamy, czy któryś z produktów systemu pokrywa się z znalezionymi produktami
        common_products = set(found_products).intersection(system_products)
        if common_products:
            score = len(common_products)  # Liczba wspólnych produktów jako wynik
            matching_systems.append((page_num, system_intent, score))
            logger.debug(f"System '{system_intent}' ma {score} wspólnych produktów: {common_products}")
    
    # Sortujemy systemy według liczby wspólnych produktów (malejąco)
    matching_systems.sort(key=lambda x: x[2], reverse=True)
    
    if not matching_systems:
        logger.warning(f"⚠️ Nie znaleziono systemów dla produktów: {found_products}")
        return None
    
    # Zwracamy top 3 systemy
    top_systems = matching_systems[:3]
    logger.info(f"🔍 Znaleziono {len(top_systems)} systemów dla '{user_text}'")
    
    return top_systems

def search_products(sender_id, user_text, return_products_only=False):
    user_text = user_text.lower()
    if user_text.startswith("⚠️"):
        logger.debug(f"Skipped processing error message: {user_text}")
        return [] if return_products_only else None
    
    found_products = []
    search_keywords = []
    
    # Szukamy produktów na podstawie słów kluczowych
    for keyword, products in keyword_to_products.items():
        if keyword.lower() in user_text:
            found_products.extend(products)
            search_keywords.append(keyword)
            logger.debug(f"🔑 Znaleziono słowo kluczowe: '{keyword}' -> {len(products)} produktów")
    
    # Deduplicate products
    found_products = list(set(found_products))
    
    # Szukamy bezpośrednio po nazwach produktów
    for product_name in products_data.keys():
        if product_name.lower() in user_text:
            if product_name not in found_products:
                found_products.append(product_name)
                logger.debug(f"🎯 Znaleziono produkt po nazwie: '{product_name}'")
    
    if return_products_only:
        return found_products
    
    if not found_products:
        logger.warning(f"⚠️ Nie znaleziono produktów dla zapytania: '{user_text}'")
        return None
    
    logger.info(f"🔍 Znaleziono {len(found_products)} produktów dla '{user_text}'")
    return found_products[:10]  # Limit to 10 products

def send_message(sender_id, message_text):
    """Send text message to user"""
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        'recipient': {'id': sender_id},
        'message': {'text': message_text}
    }
    
    url = f'https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}'
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"✅ Wiadomość wysłana do {sender_id}: {message_text[:50]}...")
        else:
            logger.error(f"❌ Błąd wysyłania: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"❌ Wyjątek podczas wysyłania wiadomości: {e}")

def send_image(sender_id, image_url):
    """Send image to user"""
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        'recipient': {'id': sender_id},
        'message': {
            'attachment': {
                'type': 'image',
                'payload': {
                    'url': image_url,
                    'is_reusable': True
                }
            }
        }
    }
    
    url = f'https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}'
    
    try:
        logger.info(f"📤 Próba wysłania obrazu: {image_url}")
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"✅ Obraz wysłany do {sender_id}: {image_url}")
        else:
            logger.error(f"❌ Błąd wysyłania: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"❌ Wyjątek podczas wysyłania obrazu: {e}")

def send_quick_replies(sender_id, message_text, quick_replies):
    """Send message with quick reply buttons"""
    headers = {
        'Content-Type': 'application/json',
    }
    
    quick_reply_list = []
    for reply in quick_replies:
        quick_reply_list.append({
            "content_type": "text",
            "title": reply[:20],  # Facebook limit
            "payload": reply
        })
    
    data = {
        'recipient': {'id': sender_id},
        'message': {
            'text': message_text,
            'quick_replies': quick_reply_list
        }
    }
    
    url = f'https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}'
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"✅ Quick replies wysłane do {sender_id}")
        else:
            logger.error(f"❌ Błąd wysyłania quick replies: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"❌ Wyjątek podczas wysyłania quick replies: {e}")

def handle_message(sender_id, message_text):
    """Handle incoming message"""
    logger.info(f"📨 Otrzymano wiadomość od {sender_id}: {message_text}")
    
    # Sprawdź, czy użytkownik już był obsłużony niedawno
    current_time = time.time()
    if sender_id in seen_users:
        last_interaction = seen_users[sender_id]
        if current_time - last_interaction < 5:  # 5 sekund cooldown
            logger.info(f"⏳ Cooldown aktywny dla {sender_id}")
            return
    
    seen_users[sender_id] = current_time
    
    # Podstawowe komendy
    if message_text.lower() in ['start', 'pomoc', 'help']:
        welcome_msg = """🏗️ Witaj! 
Jestem Twoim asystentem do doboru produktów ARDEX. Mogę pomóc Ci:

🔍 Znaleźć odpowiednie produkty
📋 Dobrać kompletne systemy klejenia
💡 Udzielić informacji o zastosowaniu

Napisz czego szukasz, np.:
• "klejenie płytek w łazience"
• "uszczelnienie basenu" 
• "wyrównanie posadzki"
• "jastrych anhydrytowy"

Jak mogę Ci pomóc?"""
        send_message(sender_id, welcome_msg)
        return
    
    # Szukaj produktów
    found_products = search_products(sender_id, message_text)
    if found_products:
        # Wyślij informacje o produktach
        product_msg = f"🎯 Znalazłem {len(found_products)} produktów ARDEX:\n\n"
        for i, product_name in enumerate(found_products, 1):
            product_info = products_data.get(product_name, {})
            description = product_info.get("description", "Brak opisu")
            application = product_info.get("application", "")
            
            product_msg += f"{i}. **{product_name}**\n"
            product_msg += f"   {description[:100]}...\n"
            if application:
                product_msg += f"   Zastosowanie: {application[:80]}...\n"
            product_msg += "\n"
        
        # Podziel wiadomość jeśli jest za długa
        messages = split_message(product_msg)
        for msg in messages:
            send_message(sender_id, msg)
    
    # Szukaj systemów
    found_systems = search_systems(sender_id, message_text)
    if found_systems:
        system_msg = f"📋 Znalazłem {len(found_systems)} systemów klejenia:\n\n"
        
        for i, (page_num, system_intent, score) in enumerate(found_systems, 1):
            system_data = page_to_intent_products[page_num]
            system_msg += f"{i}. **{system_data['intent']}**\n"
            system_msg += f"   Produkty: {', '.join(system_data['products'][:3])}...\n\n"
        
        send_message(sender_id, system_msg)
        
        # Wyślij obrazy systemów
        for page_num, system_intent, score in found_systems:
            system_data = page_to_intent_products[page_num]
            image_filename = system_data.get("image")
            if image_filename:
                image_url = f"{SERVER_URL}/images/{image_filename}"
                send_image(sender_id, image_url)
                time.sleep(1)  # Delay between images
    
    # Jeśli nic nie znaleziono
    if not found_products and not found_systems:
        send_message(sender_id, """🤔 Nie znalazłem produktów dla Twojego zapytania.
Spróbuj być bardziej konkretny, np.:
• "kleje do płytek"
• "uszczelnienie łazienki"
• "wyrównanie podłogi"
• "gruntowanie betonu"

Mogę też pomóc z konkretnymi nazwami produktów ARDEX.""")

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Verify webhook
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == VERIFY_TOKEN:
            logger.info("✅ Webhook zweryfikowany")
            return challenge
        else:
            logger.error("❌ Nieprawidłowy verify token")
            return 'Error', 403
    
    elif request.method == 'POST':
        # Handle incoming messages
        data = request.get_json()
        logger.debug(f"📨 Otrzymano webhook: {json.dumps(data, indent=2)}")
        
        if 'entry' in data:
            for entry in data['entry']:
                if 'messaging' in entry:
                    for messaging_event in entry['messaging']:
                        event_id = messaging_event.get('message', {}).get('mid', 'unknown')
                        
                        # Sprawdź, czy event nie był już przetwarzany
                        if event_id in processed_events:
                            logger.debug(f"Event {event_id} już przetworzony, pomijam")
                            continue
                        
                        processed_events[event_id] = time.time()
                        
                        # Wyczyść stare eventy (starsze niż 1 godzina)
                        current_time = time.time()
                        old_events = {k: v for k, v in processed_events.items() 
                                    if current_time - v < 3600}
                        processed_events.clear()
                        processed_events.update(old_events)
                        
                        sender_id = messaging_event['sender']['id']
                        
                        if 'message' in messaging_event:
                            message = messaging_event['message']
                            if 'text' in message:
                                message_text = message['text']
                                handle_message(sender_id, message_text)
        
        return 'OK', 200

    return 'Method not allowed', 405

if __name__ == '__main__':
    logger.info("🚀 Uruchamianie aplikacji Flask...")
    app.run(host='0.0.0.0', port=5000, debug=True)
