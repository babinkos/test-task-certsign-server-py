ARG VCS_REF
FROM docker.io/python:3.9-slim-bullseye as base
ARG VCS_REF
ENV PYTHONDONTWRITEBYTECODE 1
# Enable fault handler
ENV PYTHONFAULTHANDLER 1
### Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN \
 set -ex && \
 pip install pipenv && \
 PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy && \
 pipenv run pip list && \
 ls -lah /.venv && \
 printenv && \
 ls -lah /.venv/lib/python3.9/site-packages

# TODO : use Python 3.10 distroless image instead:
FROM gcr.io/distroless/python3:debug-nonroot
ARG VCS_REF
ENV VCS_REF=${VCS_REF}
WORKDIR /app
# Copy the python packages because the distroless base image does 
COPY --from=base /.venv/lib/python3.9/site-packages /app/site-packages
# Set the Python path where the interpreter will look for the packages
ENV PYTHONPATH /app/site-packages
COPY src/sign_srv_fastapi.py src/run.py /app/
# https://fastapi.tiangolo.com/deployment/docker/ :
ENTRYPOINT ["/usr/bin/python", "run.py"]
EXPOSE 8000
HEALTHCHECK --interval=1m --timeout=3s \
  CMD /busybox/wget -o /dev/null 'http://127.0.0.1:80/health' || exit 1
LABEL org.opencontainers.image.authors="Konstantin Babin" \
  org.opencontainers.image.source="github.com:babinkos/test-task-certsign-server-py/Dockerfile" \
  org.opencontainers.image.base.name="503110391064.dkr.ecr.eu-central-1.amazonaws.com/sign-svc" \
  org.opencontainers.image.revision="${VCS_REF}"