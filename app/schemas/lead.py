from pydantic import BaseModel
from typing import Optional

class LeadCreate(BaseModel):
    name: str
    phone: str
    comment: Optional[str] = None
    recaptcha_token: Optional[str] = None
