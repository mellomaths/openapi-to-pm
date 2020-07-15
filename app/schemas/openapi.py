from typing import List

from pydantic import BaseModel


class Info(BaseModel):
    title: str
    description: str
    version: str


class Server(BaseModel):
    url: str
    description: str


class Component(BaseModel):
    schemas: dict


class OpenApiSpecification(BaseModel):
    openapi: str
    info: Info
    servers: List[Server]
    paths: dict
    components: Component
