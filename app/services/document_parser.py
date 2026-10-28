import io
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import PyPDF2
import pdfplumber
import docx


class DocumentParser:
    """Multi-format document parser supporting PDF, DOCX, TXT, MD, CSV, and JSON."""

    @staticmethod
    def parse_file(file_path: str, original_filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Parses a document file and returns a list of sections/pages with text and metadata.
        Each entry has:
            - page_number: int (1-based)
            - text: str
            - metadata: dict
        """
        path = Path(file_path)
        filename = original_filename or path.name
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return DocumentParser._parse_pdf(file_path, filename)
        elif suffix in [".docx", ".doc"]:
            return DocumentParser._parse_docx(file_path, filename)
        elif suffix in [".txt", ".md", ".markdown"]:
            return DocumentParser._parse_text(file_path, filename)
        elif suffix == ".csv":
            return DocumentParser._parse_csv(file_path, filename)
        elif suffix == ".json":
            return DocumentParser._parse_json(file_path, filename)
        else:
            # Fallback text reading
            return DocumentParser._parse_text(file_path, filename)

    @staticmethod
    def _parse_pdf(file_path: str, filename: str) -> List[Dict[str, Any]]:
        pages_data = []

        # Attempt high-fidelity parsing with pdfplumber first
        try:
            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text(layout=True) or ""
                    
                    # Also extract any tables into readable markdown / pipe-separated rows
                    tables = page.extract_tables()
                    table_texts = []
                    if tables:
                        for tbl in tables:
                            clean_tbl = [[str(cell or "").strip() for cell in row] for row in tbl if any(row)]
                            if clean_tbl:
                                formatted = "\n".join([" | ".join(row) for row in clean_tbl])
                                table_texts.append(f"\n[Table Data]:\n{formatted}\n")
                    
                    if table_texts:
                        text += "\n" + "\n".join(table_texts)

                    clean_text = text.strip()
                    if clean_text:
                        pages_data.append({
                            "page_number": idx,
                            "text": clean_text,
                            "source_filename": filename,
                            "file_type": "pdf"
                        })
        except Exception:
            pages_data = []

        # If pdfplumber didn't extract text or failed, fallback to PyPDF2
        if not pages_data:
            try:
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for idx, page in enumerate(reader.pages, start=1):
                        text = page.extract_text() or ""
                        clean_text = text.strip()
                        if clean_text:
                            pages_data.append({
                                "page_number": idx,
                                "text": clean_text,
                                "source_filename": filename,
                                "file_type": "pdf"
                            })
            except Exception as e:
                # Log or raise if both fail
                if not pages_data:
                    raise ValueError(f"Unable to extract text from PDF '{filename}': {str(e)}")

        return pages_data

    @staticmethod
    def _parse_docx(file_path: str, filename: str) -> List[Dict[str, Any]]:
        doc = docx.Document(file_path)
        paragraphs = []
        
        # Read paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                if para.style.name.startswith("Heading"):
                    paragraphs.append(f"\n### {text}\n")
                else:
                    paragraphs.append(text)

        # Read tables
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                if any(row_cells):
                    table_rows.append(" | ".join(row_cells))
            if table_rows:
                paragraphs.append("\n[Table Data]:\n" + "\n".join(table_rows) + "\n")

        full_text = "\n\n".join(paragraphs).strip()
        if not full_text:
            return []

        return [{
            "page_number": 1,
            "text": full_text,
            "source_filename": filename,
            "file_type": "docx"
        }]

    @staticmethod
    def _parse_text(file_path: str, filename: str) -> List[Dict[str, Any]]:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = ""
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read().strip()
                if content:
                    break
            except UnicodeDecodeError:
                continue

        if not content:
            return []

        # If file has markdown headers or clear page breaks, we can preserve them
        return [{
            "page_number": 1,
            "text": content,
            "source_filename": filename,
            "file_type": Path(filename).suffix.lstrip(".") or "text"
        }]

    @staticmethod
    def _parse_csv(file_path: str, filename: str) -> List[Dict[str, Any]]:
        import csv
        rows = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for r in reader:
                if any(r):
                    rows.append(" | ".join(r))
        
        return [{
            "page_number": 1,
            "text": f"CSV Dataset: {filename}\n" + "\n".join(rows),
            "source_filename": filename,
            "file_type": "csv"
        }]

    @staticmethod
    def _parse_json(file_path: str, filename: str) -> List[Dict[str, Any]]:
        import json
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        
        formatted = json.dumps(data, indent=2)
        return [{
            "page_number": 1,
            "text": f"JSON Document: {filename}\n{formatted}",
            "source_filename": filename,
            "file_type": "json"
        }]

