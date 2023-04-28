from datetime import datetime, timedelta
from typing import Union

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from fastapi import FastAPI


app = FastAPI()


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
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
