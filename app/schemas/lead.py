from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class LeadCreate(BaseModel):
    name: str
    phone: str
    comment: Optional[str] = None
    recaptcha_token: Optional[str] = None

class LeadLargeForm(BaseModel):
    name: str
    phone: str
    email: EmailStr
    file: Optional[str] = None
    form_type: Literal["large"] = "large"

class LeadSmallForm(BaseModel):
    phone: str
    form_type: Literal["small"] = "small"
