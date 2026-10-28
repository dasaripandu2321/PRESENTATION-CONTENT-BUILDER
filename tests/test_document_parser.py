import pytest
from pathlib import Path
from app.services.document_parser import DocumentParser

def test_parse_text_file(tmp_path):
    sample_file = tmp_path / "test.txt"
    sample_file.write_text("Hello presentation content builder.\nThis is a test document.", encoding="utf-8")
    
    pages = DocumentParser.parse_file(str(sample_file), "test.txt")
    assert len(pages) == 1
    assert "Hello presentation content builder." in pages[0]["text"]
    assert pages[0]["source_filename"] == "test.txt"
    assert pages[0]["page_number"] == 1

def test_parse_csv_file(tmp_path):
    sample_csv = tmp_path / "metrics.csv"
    sample_csv.write_text("Metric,Value\nRevenue,4.82B\nGrowth,28.4%", encoding="utf-8")

    pages = DocumentParser.parse_file(str(sample_csv), "metrics.csv")
    assert len(pages) == 1
    assert "Revenue | 4.82B" in pages[0]["text"]
    assert pages[0]["file_type"] == "csv"

def test_parse_json_file(tmp_path):
    sample_json = tmp_path / "config.json"
    sample_json.write_text('{"name": "DeckGenius", "version": "1.0.0"}', encoding="utf-8")

    pages = DocumentParser.parse_file(str(sample_json), "config.json")
    assert len(pages) == 1
    assert "DeckGenius" in pages[0]["text"]
    assert pages[0]["file_type"] == "json"

