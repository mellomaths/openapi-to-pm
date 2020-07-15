from fastapi.testclient import TestClient

from .helpers.body_generator import BodyGenerator

from app.main import app


client = TestClient(app)


def test_generate_postman_collection():
    data = BodyGenerator.openapi_spec()
    response = client.post('/api/v1/postman/collection', json=data)
    assert response.status_code == 201
    assert response.json() == {'title': data.get('info').get('title')}


def test_wrong_openapi_version():
    data = BodyGenerator.openapi_spec()
    data['openapi'] = '2.0.0'
    response = client.post('/api/v1/postman/collection', json=data)
    assert response.status_code == 422
    detailed_error = response.json()
    assert detailed_error['detail'][0]['msg'] == 'openapi version must be 3.0.0'
