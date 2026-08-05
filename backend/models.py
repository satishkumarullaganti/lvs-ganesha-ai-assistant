from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class RegistrationRequest(BaseModel):
    name: str
    block: str
    flat_number: str
    mobile: str
    age: int
    competition: str

    