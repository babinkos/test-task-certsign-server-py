from platform import node

# from cryptography import x509
# from cryptography.hazmat.primitives import hashes, serialization
from fastapi.testclient import TestClient

from .sign_srv_fastapi import app


client = TestClient(app)
NODE_NAME = node()
CSR_PATH = "../certs/csr_user1.pem"


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
    # x509.load_pem_x509_csr(open(CSR_PATH, "rb").read())
    csr = open(CSR_PATH, "r").read()
    response = client.put(
        "/cert/sign",
        json={"name": "user1", "csr": csr},
    )
    assert response.status_code == 200
    assert response.json()["Request from"] == "user1"
    assert response.json()["node"] == NODE_NAME
    assert response.json()["Result"].find("-----BEGIN CERTIFICATE-----") != -1
    assert response.json()["Result"].find("-----END CERTIFICATE-----") != -1
