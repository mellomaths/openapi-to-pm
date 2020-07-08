from pydantic import BaseModel


class GetHealthResponse(BaseModel):
    ok: bool
    message: str
