import base64
import logging
import os
from datetime import datetime, timedelta

# from typing import Union # we need it in python before 3.10 in case we use union types
from logging.config import dictConfig
from pathlib import Path
from platform import node

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from fastapi import FastAPI, Request, status
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "signsrv"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }


dictConfig(LogConfig().dict())
logger = logging.getLogger("signsrv")


class Item(BaseModel):
    name: str
    csr: str


app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

NODE_NAME = node()
# in Docker it would be in same folder with .py :
CA_CERT_PATH1 = "./public.crt"
CA_KEY_PATH1 = "./privatekey.pem"
# for local repo tests we can use this in gitignored folder:
CA_CERT_PATH2 = "../certs/public.crt"
CA_KEY_PATH2 = "../certs/privatekey.pem"
CA_KEY_PATH = CA_KEY_PATH1 if Path(CA_KEY_PATH1).is_file() else CA_KEY_PATH2
CA_CERT_PATH = CA_CERT_PATH1 if Path(CA_CERT_PATH1).is_file() else CA_CERT_PATH2
CA_CERT = x509.load_pem_x509_certificate(open(CA_CERT_PATH, "rb").read())
CA_KEY = serialization.load_pem_private_key(
    open(CA_KEY_PATH, "rb").read(), None, default_backend()
)
CERT_VALIDITY_DAYS = os.environ.get("CERT_VALIDITY_DAYS", 3)


def load_csr_from_str(csr_str):
    if (csr_str.find("-----BEGIN CERTIFICATE REQUEST-----") != -1) and (
        csr_str.find("-----END CERTIFICATE REQUEST-----") != -1
    ):
        result = x509.load_pem_x509_csr(csr_str.encode("ASCII"))
    else:
        result = None
        logger.debug("INVALID CSR content:")
        logger.debug(csr_str)
        raise Exception("CSR invalid")
    return result


def sign_certificate_request(csr_str):
    csr_cert = load_csr_from_str(csr_str)
    if csr_cert.is_signature_valid:
        cert = (
            x509.CertificateBuilder()
            .subject_name(csr_cert.subject)
            .issuer_name(CA_CERT.subject)
            .public_key(csr_cert.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(
                # Our certificate will be valid for 10 days
                datetime.utcnow()
                + timedelta(days=CERT_VALIDITY_DAYS)
                # Sign our certificate with our private key
            )
            .sign(CA_KEY, hashes.SHA512())
        )
    else:
        raise Exception("Certificate invalid")
    # return DER certificate
    return cert.public_bytes(serialization.Encoding.PEM)


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
async def cert_sign(item: Item):
    logger.debug(f"name: {item.name}")
    return {
        "Request from": item.name,
        "Result": sign_certificate_request(item.csr),
        "node": NODE_NAME,
    }


# CSR_PATH = "../certs/csr_user1.pem"
# csr = open(CSR_PATH, "r").read()
# print(csr)
# provides this multiline:
# -----BEGIN CERTIFICATE REQUEST-----
# MIIInjCCBIYCAQAwKjEYMBYGA1UECgwPTXkgVGVzdCBDb21wYW55MQ4wDAYDVQQD
# DAV1c2VyMTCCBCIwDQYJKoZIhvcNAQEBBQADggQPADCCBAoCggQBALLJkege2yYZ
# print(csr.encode("ASCII"))
# provides this single line bytearray:
# b'-----BEGIN CERTIFICATE REQUEST-----\nMIIInjCCBIYCAQAwKjEYMBYGA1UE
# crt = sign_certificate_request(csr)
# print(crt)
# # produce :
# # b'-----BEGIN CERTIFICATE-----\n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\nkA==\n-----END CERTIFICATE-----\n'
# print("ascii:")
# print(crt.decode("ascii"))
# # produce same but multiline:
# # -----BEGIN CERTIFICATE-----
# # MIII/TCCBOWgAwIBAgIUXq3IuG9blYtOHqfDvkHVvZcGb2wwDQYJKoZIhvcNAQEN
# # BQAwRzELMAkGA1UEBhMCREUxEzARBgNVBAgMClNvbWUtU3RhdGUxEDAOBgNVBAoM
# # B1Rlc3QgQ28xETAPBgNVBAsMCHNpZ24gc3J2MB4XDTIzMDUwNDIwNTQyN1oXDTIz
