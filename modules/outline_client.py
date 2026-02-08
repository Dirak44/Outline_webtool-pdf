"""
Outline API Client - Wrapper fuer Outline API Calls
"""
import os
import logging
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("outline-pdf.client")


class OutlineClient:
    def __init__(self):
        self.base_url = os.getenv("OUTLINE_URL", "").rstrip("/")
        self.api_token = os.getenv("OUTLINE_API_TOKEN", "")

        if not self.base_url or not self.api_token:
            raise ValueError("OUTLINE_URL und OUTLINE_API_TOKEN muessen in .env gesetzt sein")

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        logger.info(f"OutlineClient initialisiert: {self.base_url}")

    def get_collections(self) -> List[Dict]:
        """Hole alle Collections (Bereiche) aus Outline"""
        url = f"{self.base_url}/api/collections.list"

        try:
            logger.debug(f"API Request: POST {url}")
            resp = requests.post(url, headers=self.headers, json={}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            collections = data.get("data", [])
            logger.info(f"Collections geladen: {len(collections)} Stueck")
            return collections
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Laden der Collections: {e}")
            raise

    def get_documents(self, collection_id: Optional[str] = None) -> List[Dict]:
        """Hole alle Dokumente aus Outline"""
        url = f"{self.base_url}/api/documents.list"
        payload = {}
        if collection_id:
            payload["collectionId"] = collection_id

        try:
            logger.debug(f"API Request: POST {url} (payload={payload})")
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            docs = data.get("data", [])
            logger.info(f"Dokumente geladen: {len(docs)} Stueck (collection={collection_id})")
            return docs
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Laden der Dokumente: {e}")
            raise

    def get_document(self, doc_id: str) -> Dict:
        """Hole ein spezifisches Dokument mit vollem Inhalt"""
        url = f"{self.base_url}/api/documents.info"

        try:
            logger.debug(f"API Request: POST {url} (id={doc_id})")
            resp = requests.post(url, headers=self.headers, json={"id": doc_id}, timeout=10)
            resp.raise_for_status()
            doc = resp.json()["data"]
            logger.info(f"Dokument geladen: '{doc.get('title', 'Unbekannt')}' ({doc_id})")
            return doc
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Laden des Dokuments {doc_id}: {e}")
            raise

    def search_documents(self, query: str) -> List[Dict]:
        """Suche nach Dokumenten"""
        url = f"{self.base_url}/api/documents.search"

        try:
            logger.debug(f"API Suche: '{query}'")
            resp = requests.post(url, headers=self.headers, json={"query": query}, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("data", [])
            logger.info(f"Suche '{query}': {len(results)} Treffer")
            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler bei der Suche: {e}")
            raise
