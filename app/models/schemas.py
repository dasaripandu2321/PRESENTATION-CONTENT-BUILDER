from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Slide(BaseModel):
    """Schema for an individual presentation slide."""
    slide_number: int = Field(..., description="1-based index of the slide in sequence")
    title: str = Field(..., description="Action-oriented or topical slide title")
    core_takeaway: str = Field(..., description="Single highest-impact summary or conclusion for this slide")
    bullet_points: List[str] = Field(
        default_factory=list,
        description="List of concise, high-value bullet points expanding on the title and core takeaway"
    )
    visual_layout_suggestion: str = Field(
        ...,
        description="Recommended visual presentation format (e.g., 'title_hero', 'split_2_column', '3_pillar_cards', 'kpi_highlight', 'timeline_flow', 'bullet_list')"
    )
    speaker_notes: str = Field(
        ...,
        description="Detailed narrative script and speaking prompts for the presenter during delivery"
    )
    retrieved_sources: List[str] = Field(
        default_factory=list,
        description="Citations and document references that grounded this slide's content"
    )


class SlideDeck(BaseModel):
    """Root JSON Contract for the generated presentation deck."""
    deck_title: str = Field(..., description="Overarching title of the presentation deck")
    target_audience: str = Field(..., description="Intended audience profile, expertise level, and framing")
    slides: List[Slide] = Field(..., description="Sequential list of presentation slides")


class DocumentChunk(BaseModel):
    """Metadata and content for an individual chunk extracted from a source document."""
    chunk_id: str
    doc_id: str
    source_filename: str
    file_type: str
    page_number: Optional[int] = None
    chunk_index: int
    content: str
    char_count: int


class DocumentInfo(BaseModel):
    """Summary information for an ingested document in the knowledge base."""
    doc_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    total_characters: int
    upload_timestamp: str


class IngestResponse(BaseModel):
    """Response returned after processing uploaded documents."""
    status: str
    documents: List[DocumentInfo]
    total_chunks_created: int
    message: str


class SearchRequest(BaseModel):
    """Request payload for semantic vector search over ingested knowledge chunks."""
    query: str
    top_k: int = Field(default=5, ge=1, le=25)
    doc_id: Optional[str] = None


class SearchResult(BaseModel):
    """Individual retrieved chunk with similarity score and metadata."""
    chunk_id: str
    doc_id: str
    source_filename: str
    page_number: Optional[int] = None
    chunk_index: int
    content: str
    similarity_score: float


class SearchResponse(BaseModel):
    """Search response payload."""
    query: str
    results: List[SearchResult]


class GenerateDeckRequest(BaseModel):
    """Request payload to synthesize a presentation slide deck from ingested knowledge."""
    topic: str = Field(..., description="The main focus or theme of the presentation deck")
    target_audience: Optional[str] = Field(
        default="Business & Technical Decision Makers",
        description="Audience role or demographic context"
    )
    num_slides: int = Field(default=6, ge=3, le=15, description="Number of slides to generate")
    deck_tone: Optional[str] = Field(
        default="Executive",
        description="Tone of the deck: 'Executive', 'Technical', 'Keynote', 'Educational', 'Investor Pitch'"
    )
    llm_provider: Optional[str] = Field(
        default="auto",
        description="Provider to use: 'auto', 'openai', 'gemini', 'local_offline'"
    )
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Optional additional presenter instructions, focal areas, or constraints"
    )
    selected_doc_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional subset of document IDs to restrict RAG retrieval to"
    )


class ExportPPTXRequest(BaseModel):
    """Request payload to render a SlideDeck into a downloadable PPTX presentation."""
    deck: SlideDeck
    theme: Optional[str] = Field(
        default="modern_indigo",
        description="Visual style theme: 'modern_indigo', 'executive_navy', 'emerald_clean', 'sunset_warm'"
    )

