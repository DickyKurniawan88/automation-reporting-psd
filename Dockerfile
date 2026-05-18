# Menggunakan base image Python 3.11 yang ringan (sesuai devcontainer)
FROM python:3.11-slim

# Mencegah Python membuat file .pyc dan membiarkan output stdout langsung muncul
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install OS dependencies dasar untuk Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements terlebih dahulu untuk caching layer
COPY requirements.txt .

# Install dependencies Python (termasuk Playwright dan Streamlit)
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium dan dependencies OS bawahnya
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy semua file project ke dalam container
COPY . .

# Expose port Streamlit
EXPOSE 8501

# Jalankan aplikasi Streamlit
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
