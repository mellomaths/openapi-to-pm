from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from starlette.responses import RedirectResponse

from schemas.openapi import OpenApiSpecification
from schemas.health import GetHealthResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/')
def home():
    return RedirectResponse(url='/docs')


@app.get('/api/v1/health', response_model=GetHealthResponse)
def health_check():
    return {'ok': True, 'message': 'OpenAPI2Postman is up and running!'}


@app.post('/api/v1/postman/collection', status_code=201)
def generate_postman_collection(openapi: OpenApiSpecification):
    return {'title': openapi.info.title}
