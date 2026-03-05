# Gunakan image resmi Playwright yang sudah berisi Python dan dependensi OS
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

# Install xvfb (Virtual Frambuffer) untuk membuat monitor palsu
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sisa kode
COPY . .

# Command default dibungkus xvfb-run agar seakan berjalan di layar desktop
# Gunakan format shell (tanpa kurung siku) agar xvfb bisa menangkap environment variables dengan benar
CMD xvfb-run -a uvicorn scraper:app --host 0.0.0.0 --port 5000 --reload