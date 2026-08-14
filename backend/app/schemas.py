"""
Pydantic schemas for request/response validation.

These models define the exact shape of data our API expects
and returns, giving us automatic validation and clear,
self-documenting API contracts (visible in /docs).
"""

from pydantic import BaseModel
from pydantic import ConfigDict  # ✅ Pydantic V2 style
from datetime import datetime


class DocumentResponse(BaseModel):
    """
    Shape of a document record returned to the frontend
    after upload or when listing documents.
    """

    # ✅ Pydantic V2 way — replaces the old 'class Config'
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    status: str
    created_at: datetime