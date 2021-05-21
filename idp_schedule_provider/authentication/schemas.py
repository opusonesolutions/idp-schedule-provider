from pydantic import BaseModel


class TokenResponseModal(BaseModel):
    access_token: str
    token_type: str
