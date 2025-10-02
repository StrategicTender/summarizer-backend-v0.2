FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# System deps for pdf/image libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff5-dev \
    libopenjp2-7-dev \
    ghostscript \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire app (so ai_routes.py is included)
COPY . .

# Cloud Run entrypoint (WSGI)
ENV PORT=8080
CMD ["gunicorn","app:app","--bind","0.0.0.0:8080","--workers","2","--timeout","120"]
