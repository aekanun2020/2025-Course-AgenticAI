"""Response models for PyRAGDoc."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    """A single item in a content response."""
    
    type: str = Field(..., description="Type of the content")
    text: Optional[str] = Field(default=None, description="Text content")
    json: Optional[Dict[str, Any]] = Field(default=None, description="JSON content")


class ToolResponse(BaseModel):
    """Response from a tool execution."""
    
    content: List[ContentItem] = Field(..., description="Content items")
    is_error: bool = Field(default=False, description="Whether the response indicates an error")


class ErrorResponse(BaseModel):
    """Error response."""
    
    status: str = Field(default="error", description="Response status")
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")


class StatusResponse(BaseModel):
    """Status response."""
    
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Status message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")
