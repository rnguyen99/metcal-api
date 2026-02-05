"""Pydantic models used by the API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AssetBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class AssetCreate(AssetBase):
    pass


class AssetUpdate(AssetBase):
    pass


class AssetResponse(AssetBase):
    id: int


class ErrorResponse(BaseModel):
    detail: str
