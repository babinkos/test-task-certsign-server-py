from datetime import datetime, timedelta
from platform import node

from pydantic import BaseModel

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from fastapi import FastAPI
# from typing import Union # we need it in python before 3.10 in case we use union types

class Item(BaseModel):
    name: str
    csr: str


app = FastAPI()
NODE_NAME = node()

def sign_certificate_request(csr_cert, ca_cert, private_ca_key):
    cert = (
        x509.CertificateBuilder()
        .subject_name(csr_cert.subject)
        .issuer_name(ca_cert.subject)
        .public_key(csr_cert.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(
            # Our certificate will be valid for 10 days
            datetime.utcnow()
            + timedelta(days=10)
            # Sign our certificate with our private key
        )
        .sign(private_ca_key, hashes.SHA256())
    )

    # return DER certificate
    return cert.public_bytes(serialization.Encoding.DER)


@app.get("/")
async def read_root():
    return {"msg": "Hello World"}


@app.get("/healthz", status_code=204)
async def read_healthz():
    return None


@app.get("/health", status_code=200)
async def read_health():
    return {"status": "healthy", "node": NODE_NAME}


# TODO: implement cert scr extraction and signinc with CA key to return
# signed client cert valid for 3 days
@app.put("/cert/sign")  # certs/sign data={name:"", csr:""}.
async def cert_sign(item: Item ):
    # print(item)
    return {"Request from": item.name, "Result": "ok", "node": NODE_NAME}
