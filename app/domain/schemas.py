from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None
    roles: Optional[List[str]] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: Optional[str] = None
    is_active: bool
    roles: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

    @field_serializer("roles")
    def serialize_roles(self, roles):
        try:
            return [getattr(r, "name", r) for r in roles]
        except Exception:
            return roles


class CredentialCreate(BaseModel):
    user_id: int
    label: Optional[str] = None


class CredentialSecretOut(BaseModel):
    credential_id: int
    plaintext: str
    expires_at: Optional[datetime] = None


class ErrorOut(BaseModel):
    code: str
    message: str
    trace_id: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class LogoutResponse(BaseModel):
    message: str
