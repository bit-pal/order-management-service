"""Auth-related Pydantic schemas."""
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User in response (no password)."""

    id: int
    email: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """OAuth2 token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Payload extracted from JWT."""

    user_id: int | None = None
