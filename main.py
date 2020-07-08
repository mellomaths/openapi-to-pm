from typing import Optional

from fastapi import FastAPI
from openapi.models import OpenApiSpecification

app = FastAPI()


@app.get('/api/v1/health')
def health_check():
    return {'ok': True, 'message': 'OpenAPI2Postman is up and running!'}


@app.post('/api/v1/postman-collection')
def generate_postman_collection(openapi: OpenApiSpecification):
    return {'title': openapi.info.title}
