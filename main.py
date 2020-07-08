from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openapi.models import OpenApiSpecification

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/api/v1/health')
def health_check():
    return {'ok': True, 'message': 'OpenAPI2Postman is up and running!'}


@app.post('/api/v1/postman/collection', status_code=201)
def generate_postman_collection(openapi: OpenApiSpecification):
    return {'title': openapi.info.title}
