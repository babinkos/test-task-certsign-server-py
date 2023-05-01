import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "sign_srv_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="debug",
        access_log=True,
        workers=1,
        proxy_headers=True, # https://github.com/encode/uvicorn/blob/master/uvicorn/config.py#L223
    )
