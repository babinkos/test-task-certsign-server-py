# import base64
import logging
import os
from datetime import datetime, timedelta

# from typing import Union # we need it in python before 3.10 in case we use union types
from logging.config import dictConfig
from pathlib import Path
from platform import node

import uvicorn
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


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
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


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
        logger.debug("Invalid CSR PEM content:")
        logger.debug(csr_str)
        raise HTTPException(status_code=422, detail="Invalid CSR PEM content")
        # raise Exception("CSR invalid")
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
        logger.debug("Invalid CSR signature:")
        logger.debug(csr_str)
        raise HTTPException(status_code=422, detail="Invalid CSR signature")
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


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=80,
        reload=False,
        log_level="debug",
        access_log=True,
        workers=1,  # In K8s or ECS we should better run single worker per container, see : https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker#-warning-you-probably-dont-need-this-docker-image
        proxy_headers=True,  # https://github.com/encode/uvicorn/blob/master/uvicorn/config.py#L223
    )
