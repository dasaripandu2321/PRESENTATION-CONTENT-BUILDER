import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "vector_store" in data

def test_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DeckGenius" in response.text or "Presentation" in response.text

def test_generate_deck_endpoint():
    payload = {
        "topic": "Enterprise Vector Database Scaling",
        "target_audience": "Infrastructure Architects",
        "num_slides": 4,
        "deck_tone": "Technical",
        "llm_provider": "local_offline"
    }
    response = client.post("/api/generate-deck", json=payload)
    assert response.status_code == 200
    deck = response.json()
    assert "deck_title" in deck
    assert "target_audience" in deck
    assert len(deck["slides"]) == 4

def test_export_pptx_endpoint():
    deck_payload = {
        "deck": {
            "deck_title": "FastAPI PPTX Export Test",
            "target_audience": "Developers",
            "slides": [
                {
                    "slide_number": 1,
                    "title": "FastAPI Testing Slide",
                    "core_takeaway": "REST endpoint exports genuine PPTX presentations.",
                    "bullet_points": ["Verified byte stream", "Content-Disposition header validated"],
                    "visual_layout_suggestion": "title_hero",
                    "speaker_notes": "Validate binary response.",
                    "retrieved_sources": ["tests.py (p. 1)"]
                }
            ]
        },
        "theme": "modern_indigo"
    }
    response = client.post("/api/export-pptx", json=deck_payload)
    assert response.status_code == 200
    assert "presentationml.presentation" in response.headers["content-type"]
    assert len(response.content) > 1000

