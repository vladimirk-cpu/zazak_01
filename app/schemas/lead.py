from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal

class LeadCreate(BaseModel):
    name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=25)
    comment: Optional[str] = Field(None, max_length=1000)
    recaptcha_token: Optional[str] = None

class LeadLargeForm(BaseModel):
    name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=25)
    email: EmailStr = Field(..., max_length=100)
    file: Optional[str] = Field(None, max_length=255)
    form_type: Literal["large"] = "large"

class LeadSmallForm(BaseModel):
    phone: str = Field(..., max_length=25)
    form_type: Literal["small"] = "small"
