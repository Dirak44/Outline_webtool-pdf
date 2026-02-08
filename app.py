"""
FastAPI App - Outline PDF Tool
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import io
import requests

from modules.outline_client import OutlineClient

app = FastAPI(title="Outline PDF Tool")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

outline_client = OutlineClient()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/collections")
async def get_collections():
    try:
        print("\n[ENDPOINT] /api/collections aufgerufen")
        collections = outline_client.get_collections()
        print(f"[ENDPOINT] Erfolgreich {len(collections)} Collections geladen")
        return {"success": True, "data": collections}
    except Exception as e:
        print(f"[ENDPOINT ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def get_documents(collection_id: Optional[str] = None):
    try:
        print(f"\n[ENDPOINT] /api/documents aufgerufen (collection_id={collection_id})")
        documents = outline_client.get_documents(collection_id)
        print(f"[ENDPOINT] Erfolgreich {len(documents)} Dokumente geladen")
        return {"success": True, "data": documents}
    except Exception as e:
        print(f"[ENDPOINT ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/document/{doc_id}")
async def get_document(doc_id: str):
    try:
        document = outline_client.get_document(doc_id)
        return {"success": True, "data": document}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/editor/{doc_id}", response_class=HTMLResponse)
async def editor_page(request: Request, doc_id: str):
    try:
        document = outline_client.get_document(doc_id)
        return templates.TemplateResponse(
            "editor.html",
            {
                "request": request,
                "document": document,
                "doc_id": doc_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/image-proxy")
async def image_proxy(url: str):
    """Proxy für Outline-Bilder (benötigt Auth-Header)"""
    outline_url = outline_client.base_url
    if not url.startswith(outline_url) and not url.startswith("/"):
        raise HTTPException(status_code=400, detail="Nur Outline-URLs erlaubt")

    if url.startswith("/"):
        url = outline_url + url

    try:
        headers = {"Authorization": f"Bearer {outline_client.api_token}"}
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "image/png")
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type=content_type
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bild konnte nicht geladen werden: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
