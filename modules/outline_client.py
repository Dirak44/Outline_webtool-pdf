"""
Outline API Client - Wrapper für Outline API Calls
"""
import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class OutlineClient:
    def __init__(self):
        self.base_url = os.getenv("OUTLINE_URL", "").rstrip("/")
        self.api_token = os.getenv("OUTLINE_API_TOKEN", "")
        
        if not self.base_url or not self.api_token:
            raise ValueError("OUTLINE_URL und OUTLINE_API_TOKEN müssen in .env gesetzt sein")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        
        print(f"[OutlineClient] Initialisiert mit URL: {self.base_url}")
    
    def get_collections(self) -> List[Dict]:
        """Hole alle Collections (Bereiche) aus Outline"""
        url = f"{self.base_url}/api/collections.list"
        
        try:
            print(f"[API] Request zu: {url}")
            resp = requests.post(url, headers=self.headers, json={}, timeout=10)
            
            print(f"[API] Status Code: {resp.status_code}")
            print(f"[API] Response: {resp.text[:200]}...")
            
            resp.raise_for_status()
            data = resp.json()
            
            return data.get("data", [])
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Fehler beim Laden der Collections: {e}")
            raise
    
    def get_documents(self, collection_id: Optional[str] = None) -> List[Dict]:
        """
        Hole alle Dokumente aus Outline
        Wenn collection_id angegeben, nur Dokumente aus dieser Collection
        """
        url = f"{self.base_url}/api/documents.list"
        payload = {}
        if collection_id:
            payload["collectionId"] = collection_id
        
        try:
            print(f"[API] Request zu: {url}")
            print(f"[API] Payload: {payload}")
            
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            print(f"[API] Status Code: {resp.status_code}")
            print(f"[API] Response: {resp.text[:200]}...")
            
            resp.raise_for_status()
            data = resp.json()
            
            docs = data.get("data", [])
            print(f"[API] Gefundene Dokumente: {len(docs)}")
            
            return docs
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Fehler beim Laden der Dokumente: {e}")
            raise
    
    def get_document(self, doc_id: str) -> Dict:
        """Hole ein spezifisches Dokument mit vollem Inhalt"""
        url = f"{self.base_url}/api/documents.info"
        
        try:
            print(f"[API] Lade Dokument: {doc_id}")
            resp = requests.post(url, headers=self.headers, json={"id": doc_id}, timeout=10)
            
            resp.raise_for_status()
            return resp.json()["data"]
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Fehler beim Laden des Dokuments {doc_id}: {e}")
            raise
    
    def search_documents(self, query: str) -> List[Dict]:
        """Suche nach Dokumenten"""
        url = f"{self.base_url}/api/documents.search"
        
        try:
            resp = requests.post(url, headers=self.headers, json={"query": query}, timeout=10)
            resp.raise_for_status()
            return resp.json().get("data", [])
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Fehler bei der Suche: {e}")
            raise