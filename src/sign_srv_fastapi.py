# import base64
import logging
import os
import time
from datetime import datetime, timedelta

# from typing import Union # we need it in python before 3.10 in case we use union types
from logging.config import dictConfig
from pathlib import Path
from platform import node
from typing import Union

import uvicorn
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError

# from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "signsrv"
    LOG_FORMAT: str = "%(levelname)s | %(asctime)s | %(message)s"
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
            # "stream": "ext://sys.stderr",
            "stream": "ext://sys.stdout",
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
    validity: Union[int, None] = 3


app = FastAPI()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time-Seconds"] = f"{process_time:0.4f}"
    return response


# app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def is_docker():
    cgroup = Path("/proc/self/cgroup")
    res = (
        Path("/.dockerenv").is_file()
        or cgroup.is_file()
        and "docker" in cgroup.read_text()
    )
    logger.debug(f"Container detected: {res}")
    return res


NODE_NAME = node()
HTTP_PORT = (
    80 if is_docker() else 8080
)  # root permissions needed locally to bind 80 port (lower 1024)
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
CERT_VALIDITY_DAYS = int(
    os.environ.get("CERT_VALIDITY_DAYS", 3)  # if env.var unset - limit to 3 days
)


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


def sign_certificate_request(csr_str, validity):
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
                # Our certificate will be valid for requested validity if it not more that CERT_VALIDITY_DAYS
                datetime.utcnow()
                + timedelta(days=(min(validity, CERT_VALIDITY_DAYS)))
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


@app.get("/healthz/container", status_code=204)
async def read_healthz_container():
    return None


@app.get("/healthz/alb", status_code=204)
async def read_healthz_alb():
    return None


@app.get("/healthz/r53", status_code=204)
async def read_healthz_r53():
    return None


@app.get("/health", status_code=200)
async def read_health():
    return {"status": "healthy", "node": NODE_NAME}


@app.get("/health/alb", status_code=200)
async def read_health_alb():
    return {"status": "healthy", "node": NODE_NAME}


@app.get("/health/r53", status_code=200)
async def read_health_r53():
    return {"status": "healthy", "node": NODE_NAME}


# TODO: implement cert scr extraction and signinc with CA key to return
# signed client cert valid for 3 days
@app.put("/cert/sign")  # certs/sign data={name:"", csr:""}.
async def cert_sign(item: Item):
    """
    Sign certificate request with all the information:

    - **name**: client name string
    - **csr**: base64/PEM certificate like starting from -----BEGIN CERTIFICATE REQUEST-----
    - **validity**: not required, defaults to 3 if unset, will be capped by env.var if provided
    \f
    :param item: User input.
    """
    logger.debug(f"name: {item.name}")
    return {
        "Request from": item.name,
        "Result": sign_certificate_request(item.csr, item.validity),
        "node": NODE_NAME,
    }


if __name__ == "__main__":
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"][
        "fmt"
    ] = "%(levelname)s | %(asctime)s | %(message)s"
    log_config["formatters"]["default"][
        "fmt"
    ] = "%(levelname)s | %(asctime)s | %(message)s"
    log_config["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    log_config["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    log_config["handlers"]["default"]["stream"] = "ext://sys.stdout"
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=HTTP_PORT,
        reload=False,
        log_level="info",
        access_log=True,
        workers=1,  # In K8s or ECS we should better run single worker per container, see : https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker#-warning-you-probably-dont-need-this-docker-image
        proxy_headers=True,  # https://github.com/encode/uvicorn/blob/master/uvicorn/config.py#L223
        forwarded_allow_ips="*",
    )
