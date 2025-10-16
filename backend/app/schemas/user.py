from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRead(BaseModel):
    skip: int = Field(default=0)
    limit: int = Field(default=10)


class UserCreate(BaseModel):
    user_id: str
    password: str


class CreateToken(BaseModel):
    user_id: str
    password: str