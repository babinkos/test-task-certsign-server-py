from fastapi.testclient import TestClient
from platform import node
from .sign_srv_fastapi import app

client = TestClient(app)
NODE_NAME = node()


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


def test_read_health():
    # curl -v -X GET 'http://127.0.0.1:8000/health'
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "node": NODE_NAME}


def test_read_healthz():
    # curl -v -X GET 'http://127.0.0.1:8000/health'
    response = client.get("/healthz")
    assert response.status_code == 204


def test_cert_sign():
    # curl -v -X PUT -H "Content-Type: application/json" 'http://127.0.0.1:8000/cert/sign' -d '{"name":"test1","csr":"none"}'
    response = client.put(
        "/cert/sign",
        json={"name": "test1", "csr": "none"},
    )
    assert response.status_code == 200
    assert response.json() == {"Request from": "test1", "Result": "ok", "node": NODE_NAME}
