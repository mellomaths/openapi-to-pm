from typing import Optional

from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
def health_check():
    return {'ok': True, 'message': 'OpenAPI2Postman is up and running!'}
