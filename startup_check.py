"""
Startup Self-Check - Laeuft automatisch vor dem Server-Start
Prueft alle kritischen Voraussetzungen
"""
import os
import sys
import logging

logger = logging.getLogger("outline-pdf.startup")


def run_startup_checks():
    """Fuehrt alle Startup-Checks durch. Gibt True zurueck wenn alles OK."""
    checks = [
        ("ENV: OUTLINE_URL", check_outline_url),
        ("ENV: OUTLINE_API_TOKEN", check_api_token),
        ("Datei: templates/index.html", lambda: check_file("templates/index.html")),
        ("Datei: templates/editor.html", lambda: check_file("templates/editor.html")),
        ("Ordner: static/", lambda: check_dir("static")),
        ("Ordner: modules/", lambda: check_dir("modules")),
        ("Modul: outline_client", check_outline_client_import),
        ("Verbindung: Outline API", check_outline_connection),
    ]

    print("\n" + "=" * 50)
    print("  OUTLINE PDF TOOL - Startup Check")
    print("=" * 50)

    all_ok = True
    warnings = []

    for name, check_fn in checks:
        try:
            result = check_fn()
            if result is True:
                print(f"  [OK]   {name}")
            elif isinstance(result, str):
                # Warning - nicht kritisch
                print(f"  [WARN] {name}: {result}")
                warnings.append(f"{name}: {result}")
            else:
                print(f"  [FAIL] {name}")
                all_ok = False
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            all_ok = False

    print("=" * 50)

    if warnings:
        for w in warnings:
            logger.warning(f"Startup Warning: {w}")

    if all_ok:
        print("  Alle Checks bestanden - Server startet!")
    else:
        print("  FEHLER: Nicht alle Checks bestanden!")
        print("  Server wird NICHT gestartet.")
        print("=" * 50 + "\n")

    print("=" * 50 + "\n")
    return all_ok


def check_outline_url():
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv("OUTLINE_URL", "")
    if not url:
        raise ValueError("Nicht gesetzt - .env Datei pruefen")
    if not url.startswith("http"):
        raise ValueError(f"Muss mit http(s) beginnen, ist: {url}")
    return True


def check_api_token():
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("OUTLINE_API_TOKEN", "")
    if not token:
        raise ValueError("Nicht gesetzt - .env Datei pruefen")
    if len(token) < 10:
        raise ValueError("Token sieht zu kurz aus")
    return True


def check_file(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")
    return True


def check_dir(path):
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Ordner nicht gefunden: {path}")
    return True


def check_outline_client_import():
    try:
        from modules.outline_client import OutlineClient
        return True
    except ImportError as e:
        raise ImportError(f"Import fehlgeschlagen: {e}")


def check_outline_connection():
    """Testet ob die Outline API erreichbar ist"""
    from dotenv import load_dotenv
    load_dotenv()

    import requests

    url = os.getenv("OUTLINE_URL", "").rstrip("/")
    token = os.getenv("OUTLINE_API_TOKEN", "")

    if not url or not token:
        return "Uebersprungen (keine Credentials)"

    try:
        resp = requests.post(
            f"{url}/api/collections.list",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            count = len(data.get("data", []))
            return True
        elif resp.status_code == 401:
            raise ConnectionError("API Token ungueltig (401 Unauthorized)")
        elif resp.status_code == 403:
            raise ConnectionError("Zugriff verweigert (403 Forbidden)")
        else:
            return f"Unerwarteter Status: {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return "Outline nicht erreichbar (Netzwerk-Fehler)"
    except requests.exceptions.Timeout:
        return "Outline antwortet nicht (Timeout)"


if __name__ == "__main__":
    # Kann auch standalone ausgefuehrt werden: python startup_check.py
    logging.basicConfig(level=logging.INFO)
    success = run_startup_checks()
    sys.exit(0 if success else 1)
