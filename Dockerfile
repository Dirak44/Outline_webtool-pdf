# Outline PDF Tool - Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Abhängigkeiten zuerst (Layer-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# data/-Verzeichnis sicherstellen (für templates.json Volume)
RUN mkdir -p data

# Im Container muss auf 0.0.0.0 gebunden werden (Docker-Netzwerk)
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE ${PORT}

# Healthcheck: prüft ob der Server antwortet
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:8000/')" || exit 1

CMD ["python", "app.py"]
