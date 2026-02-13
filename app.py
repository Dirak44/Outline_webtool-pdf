"""
FastAPI App - Outline PDF Tool
"""
import logging
import re
import time
import json
import uuid
import os
from urllib.parse import urlparse, unquote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import io
import requests

from modules.outline_client import OutlineClient

# ===== LOGGING SETUP =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("outline-pdf")

app = FastAPI(title="Outline PDF Tool")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

outline_client = OutlineClient()

# ===== TEMPLATES (JSON) =====
TEMPLATES_FILE = os.path.join("data", "templates.json")


def load_templates():
    with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_templates(data):
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class TemplateRequest(BaseModel):
    name: str
    icon: Optional[str] = "bi-file-text"
    font: str
    fontsize: str
    margin: str


# ===== VALIDIERUNG =====
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


def validate_doc_id(doc_id: str) -> str:
    """Validiert dass doc_id ein gueltiges UUID-Format hat"""
    doc_id = doc_id.strip()
    if not UUID_PATTERN.match(doc_id):
        logger.warning(f"Ungueltige Document ID: {doc_id}")
        raise HTTPException(status_code=400, detail="Ungueltige Document ID")
    return doc_id


def validate_proxy_url(url: str, allowed_base: str) -> str:
    """Validiert und bereinigt die Proxy-URL gegen SSRF und Path Traversal"""
    url = unquote(url).strip()

    # Path Traversal verhindern
    if '..' in url or '\x00' in url:
        logger.warning(f"Path Traversal Versuch erkannt: {url}")
        raise HTTPException(status_code=400, detail="Ungueltige URL")

    # Nur relative Outline-Pfade oder URLs die mit der Outline-Base beginnen
    if url.startswith("/"):
        # Relative URL: nur bestimmte API-Pfade erlauben
        if not url.startswith("/api/"):
            logger.warning(f"Unerlaubter relativer Pfad: {url}")
            raise HTTPException(status_code=400, detail="Nur /api/ Pfade erlaubt")
        return allowed_base + url

    if url.startswith(allowed_base):
        parsed = urlparse(url)
        allowed_parsed = urlparse(allowed_base)
        # Host muss exakt matchen (kein evil.com?outline.com Trick)
        if parsed.hostname != allowed_parsed.hostname:
            logger.warning(f"Host mismatch: {parsed.hostname} != {allowed_parsed.hostname}")
            raise HTTPException(status_code=400, detail="Nur Outline-URLs erlaubt")
        return url

    logger.warning(f"URL nicht erlaubt: {url}")
    raise HTTPException(status_code=400, detail="Nur Outline-URLs erlaubt")


# ===== REQUEST LOGGING MIDDLEWARE =====
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000)

    # Nur API- und Editor-Requests loggen (nicht static files)
    path = request.url.path
    if path.startswith("/api/") or path.startswith("/editor/"):
        logger.info(f"{request.method} {path} -> {response.status_code} ({duration}ms)")

    return response


# ===== ENDPOINTS =====

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/collections")
async def get_collections():
    try:
        logger.info("Lade Collections...")
        collections = outline_client.get_collections()
        logger.info(f"{len(collections)} Collections geladen")
        return {"success": True, "data": collections}
    except Exception as e:
        logger.error(f"Fehler beim Laden der Collections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def get_documents(collection_id: Optional[str] = None):
    try:
        # Collection ID validieren falls angegeben
        if collection_id:
            collection_id = validate_doc_id(collection_id)

        logger.info(f"Lade Dokumente (collection_id={collection_id})")
        documents = outline_client.get_documents(collection_id)
        logger.info(f"{len(documents)} Dokumente geladen")
        return {"success": True, "data": documents}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden der Dokumente: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/document/{doc_id}")
async def get_document(doc_id: str):
    try:
        doc_id = validate_doc_id(doc_id)
        logger.info(f"Lade Dokument: {doc_id}")
        document = outline_client.get_document(doc_id)
        logger.info(f"Dokument geladen: {document.get('title', 'Unbekannt')}")
        return {"success": True, "data": document}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden von Dokument {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/editor/{doc_id}", response_class=HTMLResponse)
async def editor_page(request: Request, doc_id: str):
    try:
        doc_id = validate_doc_id(doc_id)
        logger.info(f"Editor geoeffnet fuer Dokument: {doc_id}")
        document = outline_client.get_document(doc_id)
        logger.info(f"Editor: Dokument '{document.get('title', 'Unbekannt')}' geladen")
        return templates.TemplateResponse(
            "editor.html",
            {
                "request": request,
                "document": document,
                "doc_id": doc_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Oeffnen des Editors fuer {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/search")
async def search_documents(q: str):
    """Volltextsuche ueber Outline API"""
    try:
        q = q.strip()
        if not q or len(q) < 2:
            raise HTTPException(status_code=400, detail="Suchbegriff muss mindestens 2 Zeichen lang sein")
        logger.info(f"Suche nach: '{q}'")
        results = outline_client.search_documents(q)
        # Outline gibt verschachtelte Ergebnisse zurueck: [{document: {...}, ...}]
        documents = [r.get("document", r) for r in results]
        logger.info(f"Suche '{q}': {len(documents)} Treffer")
        return {"success": True, "data": documents}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler bei der Suche: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/image-proxy")
async def image_proxy(url: str):
    """Proxy fuer Outline-Bilder (benoetigt Auth-Header)"""
    outline_url = outline_client.base_url

    # URL validieren
    validated_url = validate_proxy_url(url, outline_url)
    logger.info(f"Image-Proxy: Lade Bild von {validated_url[:80]}...")

    try:
        headers = {"Authorization": f"Bearer {outline_client.api_token}"}
        response = requests.get(validated_url, headers=headers, allow_redirects=True, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "image/png")

        # Nur Bild-Content-Types erlauben
        allowed_types = ["image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml"]
        if not any(ct in content_type for ct in allowed_types):
            logger.warning(f"Image-Proxy: Unerlaubter Content-Type: {content_type}")
            raise HTTPException(status_code=400, detail=f"Kein Bild-Format: {content_type}")

        # Maximale Groesse: 20MB
        content_length = len(response.content)
        if content_length > 20 * 1024 * 1024:
            logger.warning(f"Image-Proxy: Bild zu gross: {content_length} bytes")
            raise HTTPException(status_code=413, detail="Bild zu gross (max 20MB)")

        logger.info(f"Image-Proxy: Bild geladen ({content_length} bytes, {content_type})")
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type=content_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image-Proxy Fehler: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Bild konnte nicht geladen werden: {e}")


@app.get("/api/attachments.redirect")
async def proxy_attachment(id: str):
    """Proxy fuer Outline Bilder/Attachments - leitet mit Auth-Token weiter."""
    try:
        outline_url = outline_client.base_url
        url = f"{outline_url}/api/attachments.redirect?id={id}"
        headers = {"Authorization": f"Bearer {outline_client.api_token}"}

        resp = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        return Response(content=resp.content, media_type=content_type)
    except Exception as e:
        logger.error(f"Attachment Proxy Fehler {id}: {e}")
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")


# ===== TEMPLATE CRUD =====

@app.get("/api/templates")
async def get_templates():
    try:
        data = load_templates()
        return {"success": True, "data": data["templates"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/templates")
async def create_template(req: TemplateRequest):
    try:
        data = load_templates()
        new_template = {
            "id": str(uuid.uuid4())[:8],
            "name": req.name,
            "icon": req.icon,
            "font": req.font,
            "fontsize": req.fontsize,
            "margin": req.margin,
            "builtin": False,
        }
        data["templates"].append(new_template)
        save_templates(data)
        return {"success": True, "data": new_template}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/templates/{template_id}")
async def update_template(template_id: str, req: TemplateRequest):
    try:
        data = load_templates()
        for tpl in data["templates"]:
            if tpl["id"] == template_id:
                if tpl.get("builtin"):
                    raise HTTPException(status_code=400, detail="Builtin-Vorlagen koennen nicht bearbeitet werden")
                tpl["name"] = req.name
                tpl["icon"] = req.icon
                tpl["font"] = req.font
                tpl["fontsize"] = req.fontsize
                tpl["margin"] = req.margin
                save_templates(data)
                return {"success": True, "data": tpl}
        raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str):
    try:
        data = load_templates()
        for tpl in data["templates"]:
            if tpl["id"] == template_id:
                if tpl.get("builtin"):
                    raise HTTPException(status_code=400, detail="Builtin-Vorlagen koennen nicht geloescht werden")
                data["templates"].remove(tpl)
                save_templates(data)
                return {"success": True}
        raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== SERVER START =====

if __name__ == "__main__":
    import uvicorn
    from startup_check import run_startup_checks

    if not run_startup_checks():
        import sys
        sys.exit(1)

    logger.info("Server startet auf http://127.0.0.1:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
