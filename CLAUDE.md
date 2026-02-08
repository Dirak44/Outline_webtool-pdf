# Outline PDF Tool

## Was ist das?
Web-App die Outline-Wiki-Dokumente als PDF exportiert. PDFs werden client-seitig im Browser generiert (kein Pandoc/LaTeX noetig).

## Tech Stack
- **Backend:** Python 3, FastAPI, Uvicorn
- **Frontend:** Vanilla JS, Bootstrap 5, Jinja2 Templates
- **PDF-Generierung (Client):** markdown-it, html-to-pdfmake, pdfmake (alle via CDN)
- **Outline API:** REST-Client mit Bearer Token Auth
- **Tests:** pytest, httpx, FastAPI TestClient

## Starten
```bash
pip install -r requirements.txt
python app.py
```
Beim Start laeuft automatisch ein Startup-Selfcheck (ENV, Dateien, Outline-Verbindung).
Server laeuft auf `http://127.0.0.1:8000`

## Tests ausfuehren
```bash
python -m pytest tests/ -v
```

## .env Konfiguration
```
OUTLINE_URL=https://outline.royalhaas.com
OUTLINE_API_TOKEN=ol_api_...
```

## Projektstruktur
```
app.py                     # FastAPI Server (Endpoints, Image-Proxy, Validierung)
startup_check.py           # Automatischer Selftest vor Server-Start
modules/
  outline_client.py        # Outline API Wrapper (Collections, Dokumente)
templates/
  index.html               # Startseite: Dokument-Uebersicht mit Suche/Filter
  editor.html              # PDF-Editor: Vorschau + Styling-Optionen + Download
tests/
  test_app.py              # 33 Unit Tests (Validierung, Endpoints, Startup)
static/                    # Statische Dateien (aktuell leer)
```

## Architektur
1. Backend dient nur als Proxy: Outline-API-Daten + Bild-Proxy (`/api/image-proxy`)
2. Frontend holt Markdown via API, generiert PDF komplett im Browser
3. Pipeline: Markdown -> markdown-it -> HTML -> html-to-pdfmake -> pdfmake -> PDF Blob

## API Endpoints
- `GET /` - Startseite
- `GET /api/collections` - Alle Outline Collections
- `GET /api/documents?collection_id=` - Dokumente (optional gefiltert)
- `GET /api/document/{id}` - Einzelnes Dokument mit Markdown
- `GET /editor/{doc_id}` - PDF-Editor Seite
- `GET /api/image-proxy?url=` - Proxy fuer Outline-Bilder (Auth)

## Sicherheit
- **Input-Validierung:** Document IDs muessen UUID-Format haben
- **Image-Proxy:** SSRF-Schutz, Path Traversal Schutz, Content-Type Pruefung, 20MB Limit
- **Logging:** Strukturiertes Logging mit Timestamps und Log-Levels (Python logging)
- **Request Middleware:** Loggt alle API/Editor-Requests mit Dauer in ms

## PDF Features (client-seitig)
- Titelseite mit Autor
- Inhaltsverzeichnis (toggle)
- Abschnittsnummern (toggle)
- Fusszeile: Autor links, "Seite X von Y" mittig, Dokumenttitel rechts (alles konfigurierbar)
- Schriftgroesse und Seitenrand einstellbar
- Ueberschriften-Groessen (H1-H4) individuell einstellbar
- Realtime-Vorschau bei jeder Aenderung (debounced)

## Hauptseite Features
- Dokument-Uebersicht mit Karten-Layout
- Collection-Filter (Buttons)
- Suchfeld (Titel und Textvorschau)
- Leere Dokumente (nur Titel, kein Inhalt) standardmaessig ausgeblendet, per Toggle einblendbar

## Sprache
UI und Code-Kommentare sind auf Deutsch.

## Git
- Branch: `upbeat-diffie`
- Remote: origin
