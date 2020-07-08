from pydantic import BaseModel


class Info(BaseModel):
    title: str
    description: str
    version: str


class OpenApiSpecification(BaseModel):
    openapi: str
    info: Info
