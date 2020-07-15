from typing import List

from pydantic import BaseModel, validator, ValidationError


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

    @validator('openapi')
    def swagger_version_must_be_openapi(cls, v):
        if v != '3.0.0':
            raise ValueError('openapi version must be 3.0.0')
        return v
