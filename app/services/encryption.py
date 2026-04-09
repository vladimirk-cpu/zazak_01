from cryptography.fernet import Fernet
from app.core.config import settings

fernet = Fernet(settings.SECRET_KEY.encode())

def encrypt(data: str) -> str:
    if not data:
        return data
    return fernet.encrypt(data.encode()).decode()

def decrypt(data: str) -> str:
    if not data:
        return data
    return fernet.decrypt(data.encode()).decode()
