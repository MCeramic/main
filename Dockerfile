# Lekka baza z Pythonem 3.11
FROM python:3.11.11-slim

# Katalog roboczy
WORKDIR /app

# Kopiuj plik zależności
COPY requirements.txt .

# Instaluj zależności systemowe wymagane przez niektóre pakiety (np. faiss, torch)
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

# Instalacja pip + paczki
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Skopiuj cały kod źródłowy
COPY . .

# Tworzymy folder na obrazy, jeśli nie istnieje
RUN mkdir -p images

# Render automatycznie przekazuje zmienną środowiskową $PORT
EXPOSE 10000

# Uruchom Gunicorn na zmiennym porcie (Render ustawi $PORT)
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "bot:app"]
