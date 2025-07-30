# Lekki obraz bazowy z Pythonem 3.11
FROM python:3.11.11-slim

# Katalog roboczy wewnątrz kontenera
WORKDIR /app

# Skopiuj plik z zależnościami
COPY requirements.txt .

# Instalacja systemowych bibliotek potrzebnych do budowania niektórych paczek
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Aktualizacja pip i instalacja zależności Pythona
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Skopiuj cały kod aplikacji
COPY . .

# Upewnij się, że folder na obrazy istnieje
RUN mkdir -p images

# Render przekazuje port przez zmienną środowiskową $PORT
EXPOSE 10000

# Uruchom aplikację przez Gunicorn na dynamicznym porcie
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "bot:app"]
