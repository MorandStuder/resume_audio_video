"""
Tests pour l'API FastAPI.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture pour créer un client de test."""
    return TestClient(app)


def test_root_endpoint(client: TestClient) -> None:
    """Test de l'endpoint racine."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_status_endpoint(client: TestClient) -> None:
    """Test de l'endpoint de statut."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "message" in data


def test_debug_endpoint(client: TestClient) -> None:
    """Test de l'endpoint de debug."""
    response = client.get("/api/debug")
    assert response.status_code == 200
    data = response.json()
    assert "downloader_initialized" in data
    assert "settings_loaded" in data
    assert "has_email" in data
    assert "has_password" in data


def test_check_2fa_endpoint(client: TestClient) -> None:
    """Test de l'endpoint de vérification 2FA."""
    response = client.get("/api/check-2fa")
    # L'endpoint peut retourner 503 si le downloader n'est pas initialisé
    # ou 200 si tout va bien
    assert response.status_code in [200, 503]


def test_download_without_downloader(client: TestClient) -> None:
    """Test que le téléchargement échoue sans downloader initialisé."""
    from backend.main import downloader
    # Si le downloader n'est pas initialisé, ça devrait retourner 503
    if downloader is None:
        response = client.post("/api/download", json={"max_invoices": 10})
        assert response.status_code == 503
        assert "téléchargeur n'est pas initialisé" in response.json()["detail"]


def test_submit_otp_without_downloader(client: TestClient) -> None:
    """Test que submit OTP échoue sans downloader."""
    from backend.main import downloader
    if downloader is None:
        response = client.post("/api/submit-otp", json={"otp_code": "123456"})
        assert response.status_code == 503

