"""
Unit Tests fuer Outline PDF Tool
Testet Validierung, URL-Pruefung und API-Endpoints
"""
import pytest
import sys
import os

# Projektpfad hinzufuegen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException
from fastapi.testclient import TestClient


# ===== VALIDIERUNGS-TESTS =====

class TestValidateDocId:
    """Tests fuer Document ID Validierung"""

    def setup_method(self):
        from app import validate_doc_id
        self.validate = validate_doc_id

    def test_gueltige_uuid(self):
        result = self.validate("3283f2f9-c0f7-4575-b5d9-76d5aa4befcb")
        assert result == "3283f2f9-c0f7-4575-b5d9-76d5aa4befcb"

    def test_gueltige_uuid_grossbuchstaben(self):
        result = self.validate("3283F2F9-C0F7-4575-B5D9-76D5AA4BEFCB")
        assert result == "3283F2F9-C0F7-4575-B5D9-76D5AA4BEFCB"

    def test_uuid_mit_leerzeichen(self):
        result = self.validate("  3283f2f9-c0f7-4575-b5d9-76d5aa4befcb  ")
        assert result == "3283f2f9-c0f7-4575-b5d9-76d5aa4befcb"

    def test_ungueltige_uuid_zu_kurz(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("abc-123")
        assert exc.value.status_code == 400

    def test_ungueltige_uuid_leer(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("")
        assert exc.value.status_code == 400

    def test_ungueltige_uuid_sql_injection(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("'; DROP TABLE documents; --")
        assert exc.value.status_code == 400

    def test_ungueltige_uuid_path_traversal(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("../../etc/passwd")
        assert exc.value.status_code == 400

    def test_ungueltige_uuid_script(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("<script>alert(1)</script>")
        assert exc.value.status_code == 400


class TestValidateProxyUrl:
    """Tests fuer Image-Proxy URL Validierung"""

    ALLOWED_BASE = "https://outline.royalhaas.com"

    def setup_method(self):
        from app import validate_proxy_url
        self.validate = validate_proxy_url

    def test_gueltige_outline_url(self):
        url = "https://outline.royalhaas.com/api/attachments.redirect?id=abc123"
        result = self.validate(url, self.ALLOWED_BASE)
        assert result == url

    def test_gueltige_relative_api_url(self):
        result = self.validate("/api/attachments.redirect?id=abc", self.ALLOWED_BASE)
        assert result == "https://outline.royalhaas.com/api/attachments.redirect?id=abc"

    def test_ungueltige_externe_url(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("https://evil.com/malware.exe", self.ALLOWED_BASE)
        assert exc.value.status_code == 400

    def test_path_traversal(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("/api/../../../etc/passwd", self.ALLOWED_BASE)
        assert exc.value.status_code == 400

    def test_null_byte_injection(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("/api/image.png\x00.html", self.ALLOWED_BASE)
        assert exc.value.status_code == 400

    def test_unerlaubter_relativer_pfad(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("/etc/passwd", self.ALLOWED_BASE)
        assert exc.value.status_code == 400

    def test_ssrf_localhost(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("http://localhost:22/", self.ALLOWED_BASE)
        assert exc.value.status_code == 400

    def test_ssrf_internal_ip(self):
        with pytest.raises(HTTPException) as exc:
            self.validate("http://169.254.169.254/latest/meta-data/", self.ALLOWED_BASE)
        assert exc.value.status_code == 400


# ===== API ENDPOINT TESTS =====

class TestAPIEndpoints:
    """Tests fuer API Endpoints mit TestClient"""

    def setup_method(self):
        from app import app
        self.client = TestClient(app)

    def test_home_page(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert "Outline PDF Tool" in response.text

    def test_document_ungueltige_id(self):
        response = self.client.get("/api/document/not-a-uuid")
        assert response.status_code == 400
        assert "Ungueltige Document ID" in response.json()["detail"]

    def test_document_sql_injection(self):
        response = self.client.get("/api/document/'; DROP TABLE docs; --")
        assert response.status_code == 400

    def test_editor_ungueltige_id(self):
        response = self.client.get("/editor/invalid-id")
        assert response.status_code == 400

    def test_image_proxy_externe_url(self):
        response = self.client.get("/api/image-proxy?url=https://evil.com/hack.exe")
        assert response.status_code == 400

    def test_image_proxy_path_traversal(self):
        response = self.client.get("/api/image-proxy?url=/../../etc/passwd")
        assert response.status_code == 400

    def test_image_proxy_ohne_url(self):
        response = self.client.get("/api/image-proxy")
        assert response.status_code == 422  # Missing required parameter

    def test_collections_endpoint(self):
        """Collections Endpoint muss antworten (200 oder 500 bei API-Fehler)"""
        response = self.client.get("/api/collections")
        assert response.status_code in [200, 500]

    def test_documents_endpoint(self):
        """Documents Endpoint muss antworten"""
        response = self.client.get("/api/documents")
        assert response.status_code in [200, 500]

    def test_documents_ungueltige_collection_id(self):
        response = self.client.get("/api/documents?collection_id=not-valid")
        assert response.status_code == 400


# ===== STARTUP SELF-TEST =====

class TestStartupChecks:
    """Tests die beim Startup geprueft werden"""

    def test_env_outline_url_gesetzt(self):
        from dotenv import load_dotenv
        load_dotenv()
        url = os.getenv("OUTLINE_URL", "")
        assert url, "OUTLINE_URL muss in .env gesetzt sein"
        assert url.startswith("http"), "OUTLINE_URL muss mit http(s) beginnen"

    def test_env_api_token_gesetzt(self):
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("OUTLINE_API_TOKEN", "")
        assert token, "OUTLINE_API_TOKEN muss in .env gesetzt sein"
        assert len(token) > 10, "OUTLINE_API_TOKEN sieht zu kurz aus"

    def test_templates_vorhanden(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assert os.path.isfile(os.path.join(base, "templates", "index.html")), "templates/index.html fehlt"
        assert os.path.isfile(os.path.join(base, "templates", "editor.html")), "templates/editor.html fehlt"

    def test_static_ordner_vorhanden(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assert os.path.isdir(os.path.join(base, "static")), "static/ Ordner fehlt"

    def test_modules_vorhanden(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assert os.path.isfile(os.path.join(base, "modules", "outline_client.py")), "modules/outline_client.py fehlt"

    def test_outline_client_import(self):
        """OutlineClient muss importierbar sein"""
        from modules.outline_client import OutlineClient
        assert OutlineClient is not None

    def test_app_import(self):
        """FastAPI App muss importierbar sein"""
        from app import app
        assert app is not None
        assert app.title == "Outline PDF Tool"
