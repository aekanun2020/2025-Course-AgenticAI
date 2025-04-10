"""Document models for PyRAGDoc."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    
    source: Optional[str] = Field(default=None, description="Source of the document")
    url: Optional[str] = Field(default=None, description="URL of the document")
    title: Optional[str] = Field(default=None, description="Title of the document")
    author: Optional[str] = Field(default=None, description="Author of the document")
    created_at: Optional[datetime] = Field(default=None, description="Creation date")
    file_type: Optional[str] = Field(default=None, description="File type")
    page_number: Optional[int] = Field(default=None, description="Page number for PDFs")
    section: Optional[str] = Field(default=None, description="Section name")
    tags: List[str] = Field(default_factory=list, description="Tags for the document")
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class DocumentChunk(BaseModel):
    """A chunk of a document with its content and metadata."""
    
    text: str = Field(..., description="Text content of the chunk")
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    timestamp: datetime = Field(default_factory=datetime.now)
    id: Optional[str] = Field(default=None, description="Unique identifier")


class SearchQuery(BaseModel):
    """Search query parameters."""
    
    query: str = Field(..., description="Search query text")
    limit: int = Field(default=5, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Filters for metadata"
    )
    min_score: Optional[float] = Field(
        default=None, 
        description="Minimum similarity score"
    )


class SearchResult(BaseModel):
    """Search result with document chunk and score."""
    
    chunk: DocumentChunk
    score: float = Field(..., description="Similarity score")
