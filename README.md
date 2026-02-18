# Outline PDF Tool

Web-App zum Exportieren von [Outline](https://www.getoutline.com/)-Dokumenten als PDF.
Die PDFs werden vollständig im Browser generiert – kein LaTeX oder Pandoc nötig.

---

## Features

- 📄 Einzelne Dokumente als PDF exportieren
- 📦 Mehrere Dokumente als ZIP-Batch-Export
- 🎨 Vollständig anpassbares Layout (Schriftart, Schriftgröße, Ränder, Kopf-/Fußzeile)
- 📑 Automatisches Inhaltsverzeichnis und Abschnittsnummern
- 💾 Vorlagen speichern und wiederverwenden
- 🌙 Dark/Light Mode
- ⭐ Favoriten-System

---

## Installation mit Docker (empfohlen)

### Voraussetzungen

- Docker + Docker Compose auf dem Server installiert
- Outline API Token ([Anleitung](#outline-api-token-erstellen))

### 1. docker-compose.yml herunterladen

Lade nur diese eine Datei auf deinen Server:

```bash
curl -O https://raw.githubusercontent.com/Dirak44/outline-pdf/main/docker-compose.yml
```

Oder erstelle sie manuell mit folgendem Inhalt:

```yaml
services:
  outline-pdf:
    image: ghcr.io/dirak44/outline-pdf:latest
    container_name: outline-pdf
    restart: unless-stopped
    ports:
      - "8080:8000"
    environment:
      OUTLINE_URL: "https://deine-outline-instanz.example.com"
      OUTLINE_API_TOKEN: "ol_api_DEIN_TOKEN_HIER"
      RESET_TEMPLATES_ON_START: "false"
    volumes:
      - outline-pdf-data:/app/data

volumes:
  outline-pdf-data:
```

### 2. Konfiguration anpassen

Öffne `docker-compose.yml` und trage deine Werte ein:

| Variable | Beschreibung |
|---|---|
| `OUTLINE_URL` | URL deiner Outline-Instanz (z.B. `https://wiki.example.com`) |
| `OUTLINE_API_TOKEN` | Dein Outline API Token (siehe unten) |
| `RESET_TEMPLATES_ON_START` | `true` = Custom-Vorlagen beim Start löschen, `false` = behalten |
| Port `8080` | Externer Port auf dem Host (links vom `:`) – nach Wunsch ändern |

### 3. Starten

```bash
docker compose up -d
```

Die App ist dann erreichbar unter: `http://deine-server-ip:8080`

### Updates einspielen

```bash
docker compose pull && docker compose up -d
```

---

## Outline API Token erstellen

1. In Outline einloggen
2. **Einstellungen** → **API** → **Neues Token erstellen**
3. Token kopieren und in die `docker-compose.yml` eintragen

---

## Lokale Installation (Entwicklung)

### Voraussetzungen

- Python 3.11+
- pip

### Setup

```bash
# Repository klonen
git clone https://github.com/Dirak44/outline-pdf.git
cd outline-pdf

# Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration anlegen
cp .env.example .env
# .env mit Editor öffnen und Werte eintragen
```

### Starten

```bash
python app.py
```

App läuft auf: `http://127.0.0.1:8000`

### Tests ausführen

```bash
python -m pytest tests/ -v
```

---

## Nutzung

### Dokument als PDF exportieren

1. App öffnen → Dokument aus der Liste auswählen
2. Im Editor das Layout anpassen (Schriftart, Ränder, Kopf-/Fußzeile etc.)
3. **PDF herunterladen** klicken

### Mehrere Dokumente exportieren (Batch)

1. Auf der Hauptseite Dokumente per Checkbox auswählen
2. **Als ZIP exportieren** klicken
3. Fortschrittsbalken abwarten → ZIP wird automatisch heruntergeladen

### Vorlagen speichern

1. Layout im Editor wunschgemäß einstellen
2. **Als Vorlage speichern** klicken → Name vergeben
3. Vorlage steht auf der linken Seite zur Auswahl bereit

---

## Integration in bestehendes Outline Docker-Setup

Wenn Outline bereits per Docker Compose läuft, kannst du den Service direkt einbinden.
Füge den `outline-pdf`-Block in deine bestehende `docker-compose.yml` ein:

```yaml
services:
  # ... deine bestehenden Services (outline, postgres, redis etc.) ...

  outline-pdf:
    image: ghcr.io/dirak44/outline-pdf:latest
    container_name: outline-pdf
    restart: unless-stopped
    ports:
      - "8080:8000"
    environment:
      OUTLINE_URL: "http://outline:3000"  # interner Docker-Hostname
      OUTLINE_API_TOKEN: "ol_api_DEIN_TOKEN_HIER"
    volumes:
      - outline-pdf-data:/app/data
    networks:
      - outline_default  # gleiches Netzwerk wie Outline

volumes:
  outline-pdf-data:
```

> **Tipp:** Mit `docker network ls` siehst du den Namen des bestehenden Outline-Netzwerks.

---

## Tech Stack

- **Backend:** Python 3, FastAPI, Uvicorn
- **Frontend:** Vanilla JS, Bootstrap 5
- **PDF-Generierung:** markdown-it, html-to-pdfmake, pdfmake (alle via CDN, läuft im Browser)
- **Outline API:** REST mit Bearer Token

---

## Sicherheitshinweis

Die `.env`-Datei enthält deinen API Token und darf **niemals** ins Git-Repository eingecheckt werden.
Sie ist in `.gitignore` eingetragen und wird beim Docker-Build ignoriert.
Verwende immer Umgebungsvariablen oder Docker Secrets für sensible Daten.
