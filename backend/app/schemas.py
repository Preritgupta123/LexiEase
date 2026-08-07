"""
Pydantic schemas for request/response validation.

These models define the exact shape of data our API expects
and returns, giving us automatic validation and clear,
self-documenting API contracts (visible in /docs).
"""

from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    """
    Shape of a document record returned to the frontend
    after upload or when listing documents.
    """
    id: str
    file_name: str
    status: str
    created_at: datetime

    class Config:
        # Allows Pydantic to read data directly from
        # Supabase's response objects (dict-like access)
        from_attributes = True