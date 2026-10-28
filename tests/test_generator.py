import pytest
from app.services.generator import SlideDeckGenerator
from app.models.schemas import GenerateDeckRequest, SlideDeck

def test_slide_deck_generation():
    generator = SlideDeckGenerator()
    req = GenerateDeckRequest(
        topic="Scalable Multi-Agent Enterprise Architecture",
        target_audience="Executive Leadership",
        num_slides=5,
        deck_tone="Executive",
        llm_provider="local_offline"
    )

    deck = generator.generate_deck(req)

    # Validate Schema
    assert isinstance(deck, SlideDeck)
    assert len(deck.slides) == 5
    assert deck.target_audience == "Executive Leadership"
    assert "Scalable Multi-Agent" in deck.deck_title

    # Validate individual slide contract fields
    for slide in deck.slides:
        assert isinstance(slide.slide_number, int)
        assert len(slide.title) > 0
        assert len(slide.core_takeaway) > 0
        assert isinstance(slide.bullet_points, list)
        assert len(slide.bullet_points) >= 1
        assert len(slide.visual_layout_suggestion) > 0
        assert len(slide.speaker_notes) > 0
        assert isinstance(slide.retrieved_sources, list)

