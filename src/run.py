import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "sign_srv_fastapi:app",
        host="0.0.0.0",
        port=80,
        reload=False,
        log_level="info",
        access_log=False,
        workers=1, # In K8s or ECS we should better run single worker per container, see : https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker#-warning-you-probably-dont-need-this-docker-image
        proxy_headers=True, # https://github.com/encode/uvicorn/blob/master/uvicorn/config.py#L223
    )
