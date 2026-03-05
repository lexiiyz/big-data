# Gunakan image resmi Playwright yang sudah berisi Python dan dependensi OS
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sisa kode
COPY . .

# Command default saat container menyala sebagai API Server
CMD ["uvicorn", "scraper:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]