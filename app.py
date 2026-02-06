"""
FastAPI App - Outline PDF Tool
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import os

from modules.outline_client import OutlineClient
from modules.pdf_generator import PDFGenerator

app = FastAPI(title="Outline PDF Tool")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

outline_client = OutlineClient()
pdf_generator = PDFGenerator()


class PDFStyleRequest(BaseModel):
    document_id: str
    margin: Optional[str] = "2.5cm"
    fontsize: Optional[str] = "11pt"
    font: Optional[str] = "Arial"


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


@app.post("/api/generate-pdf")
async def generate_pdf(request: PDFStyleRequest):
    try:
        document = outline_client.get_document(request.document_id)
        
        style = {
            "margin": request.margin,
            "fontsize": request.fontsize,
            "font": request.font,
        }
        
        pdf_path = pdf_generator.generate_pdf(
            markdown_text=document.get("text", ""),
            title=document.get("title", "Dokument"),
            style=style
        )
        
        return {
            "success": True, 
            "pdf_path": pdf_path,
            "filename": os.path.basename(pdf_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{filename}")
async def download_pdf(filename: str):
    pdf_path = os.path.join("output", filename)
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    
    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)