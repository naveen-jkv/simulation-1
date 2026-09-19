from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["John Doe"])
    email: EmailStr = Field(..., examples=["john.doe@college.edu"])
    password: str = Field(..., min_length=6, max_length=128, examples=["Secret123!"])
    role: Optional[Literal["student", "admin"]] = Field(
        default="student",
        description="User role: 'student' or 'admin'",
        examples=["student"],
    )


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["john.doe@college.edu"])
    password: str = Field(..., examples=["Secret123!"])


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
