# Użyj lekkiego obrazu z Pythona 3.11
FROM python:3.11.11-slim

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj plik z zależnościami
COPY requirements.txt .

# Zainstaluj potrzebne biblioteki systemowe (dla zależności pip)
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

# Zainstaluj zależności Pythona
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Skopiuj resztę plików projektu
COPY . .

# Upewnij się, że folder z obrazami istnieje
RUN mkdir -p images

# Render wymaga nasłuchiwania na porcie przekazanym przez zmienną środowiskową $PORT
EXPOSE 10000

# Uruchom Gunicorn, używając zmiennej środowiskowej PORT
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "bot:app"]
