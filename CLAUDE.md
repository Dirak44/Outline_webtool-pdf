# Outline PDF Tool

## Arbeitsweise
- **Beim Start immer `TODO.md` lesen** und offene Tasks der Reihe nach abarbeiten
- **Nach jeder abgeschlossenen Änderung einen Commit auf `main`** machen mit aussagekräftiger Commit-Message
- Commit-Format: `feat:`, `fix:`, `docs:`, `test:`, `refactor:` je nach Art der Änderung
- UI-Texte auf Deutsch mit korrekten Umlauten (ü, ö, ä, ß)

## Was ist das?
Web-App die Outline-Wiki-Dokumente als PDF exportiert. PDFs werden client-seitig im Browser generiert (kein Pandoc/LaTeX nötig).

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
Beim Start läuft automatisch ein Startup-Selfcheck (ENV, Dateien, Templates, Outline-Verbindung).
Server läuft auf `http://127.0.0.1:8000`

## Tests ausführen
```bash
python -m pytest tests/ -v
```

## .env Konfiguration
```
OUTLINE_URL=https://outline.royalhaas.com
OUTLINE_API_TOKEN=ol_api_...
RESET_TEMPLATES_ON_START=false   # true = Custom-Vorlagen beim Start löschen
```

## Projektstruktur
```
app.py                     # FastAPI Server (Endpoints, Image-Proxy, Template-CRUD, Validierung)
startup_check.py           # Automatischer Selftest vor Server-Start (inkl. Template-Reset)
modules/
  outline_client.py        # Outline API Wrapper (Collections, Dokumente mit Pagination)
templates/
  index.html               # Startseite: Dokument-Übersicht mit Suche/Filter
  editor.html              # PDF-Editor: Vorschau + Styling-Optionen + Download
tests/
  test_app.py              # 41+ Unit Tests (Validierung, Endpoints, Templates, Startup)
static/
  css/theme.css            # Dark/Light Mode CSS-Variablen
  js/theme.js              # Theme-Toggle mit System-Erkennung und localStorage
data/
  templates.json           # PDF-Vorlagen (Builtin + Custom, JSON Storage)
```

## Architektur
1. Backend dient nur als Proxy: Outline-API-Daten + Bild-Proxy (`/api/image-proxy`)
2. Frontend holt Markdown via API, generiert PDF komplett im Browser
3. Pipeline: Markdown → markdown-it → HTML → html-to-pdfmake → pdfmake → PDF Blob
4. Vorlagen werden in `data/templates.json` gespeichert (Builtin + Custom)

## API Endpoints
- `GET /` – Startseite
- `GET /api/collections` – Alle Outline Collections
- `GET /api/documents?collection_id=` – Dokumente (optional gefiltert, mit Pagination)
- `GET /api/document/{id}` – Einzelnes Dokument mit Markdown
- `GET /editor/{doc_id}` – PDF-Editor Seite
- `GET /api/search?q=` – Volltextsuche über Outline API
- `GET /api/image-proxy?url=` – Proxy für Outline-Bilder (Auth)
- `GET /api/attachments.redirect?id=` – Proxy für Outline Attachments
- `GET /api/templates` – Alle Vorlagen laden
- `POST /api/templates` – Neue Vorlage erstellen
- `PUT /api/templates/{id}` – Vorlage bearbeiten (nur Custom)
- `DELETE /api/templates/{id}` – Vorlage löschen (nur Custom)

## Sicherheit
- **Input-Validierung:** Document IDs müssen UUID-Format haben
- **Image-Proxy:** SSRF-Schutz, Path Traversal Schutz, Content-Type Prüfung, 20MB Limit
- **Template-Schutz:** Builtin-Vorlagen können nicht bearbeitet oder gelöscht werden
- **Logging:** Strukturiertes Logging mit Timestamps und Log-Levels (Python logging)
- **Request Middleware:** Loggt alle API/Editor-Requests mit Dauer in ms

## PDF Features (client-seitig)
- Erweitertes Deckblatt (Titel, Untertitel, Autor, Organisation, Abteilung, Betreuer, Datum)
- Inhaltsverzeichnis (toggle)
- Abschnittsnummern (toggle)
- Schriftart-Auswahl (Roboto, Times New Roman, Helvetica, Courier)
- Schriftgröße, Zeilenabstand und Seitenrand einstellbar
- Überschriften-Größen (H1–H4) individuell einstellbar
- Kopfzeile: 3 Felder (links/mitte/rechts) frei konfigurierbar
- Fußzeile: 3 Felder (links/mitte/rechts) frei konfigurierbar
- Felder-Optionen: Autor, Titel, Organisation, Datum, Seitenzahl, eigener Text
- PDF-Metadaten (Titel, Autor, Betreff, Erstelldatum) eingebettet
- Export-Einstellungen pro Dokument in localStorage gespeichert
- Realtime-Vorschau bei jeder Änderung (debounced)

## Dark/Light Mode
- Automatische Erkennung der System-Einstellung (prefers-color-scheme)
- Manueller Toggle-Button in der Navbar (Sonne/Mond Icon)
- Persistenz via localStorage (manueller Override bleibt erhalten)
- Beide Seiten (Hauptseite + Editor) unterstützt

## Hauptseite Features
- Dokument-Übersicht mit Karten-Layout
- Collection-Filter (Buttons)
- Suchfeld mit Backend-Volltextsuche (ab 2 Zeichen, Debounce 400ms)
- Leere Dokumente (nur Titel, kein Inhalt) standardmäßig ausgeblendet, per Toggle einblendbar
- Vollständige Pagination: Lädt ALLE Dokumente (auch Collections mit 50+ Seiten)
- Favoriten-System: Stern-Button auf Karten, localStorage persistent, Filter-Toggle
- Batch-Export: Checkboxen zur Mehrfachauswahl, ZIP-Download mit Fortschrittsbalken (JSZip + pdfmake)

## Custom Vorlagen System
- 3 Builtin-Vorlagen: Standard, Formell, Minimal (nicht löschbar)
- Custom-Vorlagen erstellen: Aktuelle Editor-Einstellungen als Vorlage speichern
- Custom-Vorlagen löschen: X-Button auf der Vorlage
- Gespeichert in `data/templates.json` (persistent über Server-Neustarts)
- `RESET_TEMPLATES_ON_START=true` in .env löscht Custom-Vorlagen beim Start

## Sprache
UI und Code-Kommentare sind auf Deutsch mit korrekten Umlauten (ü, ö, ä, ß).

## Git
- Branch: `main`
- Remote: origin
