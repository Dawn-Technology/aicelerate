from pydantic import BaseModel, EmailStr


class Customer(BaseModel):
    id: int
    name: str
    email: EmailStr
    city: str | None = None
