# test-task-certsign-server-py

## Description

This project implemented with FastApi for educational purpose. All sources stored in [./src](https://github.com/babinkos/test-task-certsign-server-py/tree/main/src) folder.
Required Python packages listed in `requirements.txt` and `Pipfile` (which then used in Dockerfile).

This Api `/cert/sign` endpoint implements Certificate signing with CA key (this key should be generated locally with `prepare-ca-crt.sh` script).

Request JSON schema is defined in this class [Item](https://github.com/babinkos/test-task-certsign-server-py/blob/be28b90e12b950b5066e292a30bca0b88f8e8b32/src/sign_srv_fastapi.py#L59):
```
class Item(BaseModel):
    name: str
    csr: str
    validity: Union[int, None] = 3
```

where `name` is a client name id for loggin purpose, `csr` is a PEM encoded CSR, with content like 
```
-----BEGIN CERTIFICATE REQUEST-----\nMIII...
```
parameter `validity` is optional, you can request certificate duration in days with it.

Environment variable `CERT_VALIDITY_DAYS` might be provided and requested `validity` for CSR can't exceed that value. If unset `CERT_VALIDITY_DAYS` defaults to `3` days.


Here is an example of curl command to send request to service:
```
curl -v -X PUT -H "Content-Type: application/json" 'http://127.0.0.1:8080/cert/sign' -d '{"name":"test1","csr":"none"}'
```
It will produce this output :
```
*   Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to 127.0.0.1 (127.0.0.1) port 8080 (#0)
> PUT /cert/sign HTTP/1.1
> Host: 127.0.0.1:8080
> User-Agent: curl/7.58.0
> Accept: */*
> Content-Type: application/json
> Content-Length: 29
> 
* upload completely sent off: 29 out of 29 bytes
< HTTP/1.1 422 Unprocessable Entity
< date: Wed, 10 May 2023 14:24:29 GMT
< server: uvicorn
< content-length: 36
< content-type: application/json
< x-process-time-seconds: 0.0024
```
Where addinional response header `x-process-time-seconds` provides seconds spent on csr processing.

```
curl -v -X PUT -H "Content-Type: application/json" 'http://127.0.0.1:8080/cert/sign' -d @test-curl-data.json
```
Will provide output :
```
  Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to 127.0.0.1 (127.0.0.1) port 8080 (#0)
> PUT /cert/sign HTTP/1.1
> Host: 127.0.0.1:8080
> User-Agent: curl/7.58.0
> Accept: */*
> Content-Type: application/json
> Content-Length: 1687
> Expect: 100-continue
> 
< HTTP/1.1 100 Continue
* We are completely uploaded and fine
< HTTP/1.1 200 OK
< date: Wed, 10 May 2023 14:23:59 GMT
< server: uvicorn
< content-length: 1954
< content-type: application/json
< x-process-time-seconds: 0.0443
< 
{"Request from":"test2-f54fa3ca-2726-454c-bddc-a20da841e1a0","Result":"-----BEGIN CERTIFICATE-----\nMII...\n-----END CERTIFICATE-----\n","node":"laptop.home.arpa"}
```
(certificate content omitted)

## How-to run locally

Depending of you environment use one of this commands from [./src](https://github.com/babinkos/test-task-certsign-server-py/tree/main/src) :
- `pipenv run python sign_srv_fastapi.py`
- `python sign_srv_fastapi.py`

## How-to build container image

1. Run `prepare-ca-crt.sh` to prepare CA cert first
2. Run `docker-arm64.sh` if you need to build ARM64 arch image or skip it.
3. Update tags in `local-build.sh` and trun it to build container images

## How-to run container locally

Run it this way once built `docker run -it --rm -p 8080:80 503110391064.dkr.ecr.eu-central-1.amazonaws.com/sign-svc:amd64`
Where `-p 8080:80` option will map container port 80 to port 8080 on your laptop.

And for Arm64 arch add `--platform linux/arm64` to parameters.

to evaluate memory consumption use `docker stats <container id>`

## TODO list

1. Get CA cert and key from AWS SSM Parameter Store.
2. Improve code coverage.
3. Add gzip support.
4. Maybe - rewrite in Go.
