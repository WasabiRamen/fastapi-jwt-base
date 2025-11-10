from pydantic import BaseModel

class CreateAccount(BaseModel):
    token: str
    user_id: str
    user_name: str
    password: str
    email: str
    phone_number: str | None = None
