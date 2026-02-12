# TODO - Outline PDF Tool

## Erledigt
- [x] FastAPI Backend mit Outline API Integration
- [x] Dokumenten-Browser (Hauptseite) mit Suche und Collection-Filter
- [x] PDF-Editor mit Live-Vorschau
- [x] Client-seitige PDF-Generierung mit pdfmake (Pandoc entfernt)
- [x] Leere Dokumente auf Hauptseite ausblenden (Toggle zum Einblenden)
- [x] Image-Proxy mit SSRF-Schutz und Content-Type Validierung
- [x] UUID-Validierung gegen SQL-Injection und Path-Traversal
- [x] Startup Self-Check System
- [x] Titelseite, Inhaltsverzeichnis, Abschnittsnummern, Footer
- [x] Heading-Groessen konfigurierbar (H1-H4)
- [x] Debounced Live-Vorschau (400ms)
- [x] Request-Logging Middleware
- [x] CLAUDE.md und TODO.md erstellt
- [x] Dark/Light Mode mit automatischer System-Erkennung (prefers-color-scheme) und localStorage Persistenz
- [x] Vollstaendige Pagination fuer Outline API (alle Dokumente laden, auch 50+)
- [x] Custom Template System (erstellen/bearbeiten/loeschen) mit JSON Storage
- [x] .env Option RESET_TEMPLATES_ON_START zum Zuruecksetzen der Vorlagen beim Start abschaltbar
- [x] Unit Tests (33+ Tests: Security, Validierung, Endpoints, Templates, Startup)

## Offen
- [ ] Schriftart-Auswahl im Editor (aktuell nur ueber Templates)
- [ ] Dokumenten-Suche im Backend nutzen (search_documents ist implementiert aber nicht in UI)
- [ ] PDF-Export: Benutzerdefinierte Kopfzeile
- [ ] Favoriten-System fuer haeufig genutzte Dokumente
- [ ] Batch-Export: Mehrere Dokumente gleichzeitig als PDF
