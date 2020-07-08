from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.json() == {'ok': True, 'message': 'OpenAPI2Postman is up and running!'}


def test_generate_postman_collection():
    data = {
        "openapi": "3.0.0",
        "info": {
            "title": "API Orders",
            "description": "API to handle Orders operations.",
            "version": "1.0.0"
        }
    }
    response = client.post('/api/v1/postman/collection', json=data)
    assert response.status_code == 201
    assert response.json() == {'title': data.get('info').get('title')}
