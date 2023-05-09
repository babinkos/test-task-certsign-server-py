#! /usr/bin/env bash
# docker build --no-cache --progress plain -f Dockerfile -t 503110391064.dkr.ecr.eu-central-1.amazonaws.com/sign-svc:latest .
# docker buildx build --platform linux/amd64 --no-cache --progress plain -f Dockerfile -t sign-svc:amd64 .
# docker buildx build --platform linux/arm64 --no-cache --progress plain -f Dockerfile-arm64 -t sign-svc:arm64 .
docker build --platform linux/arm64 --no-cache --progress plain -f Dockerfile-arm64 -t 503110391064.dkr.ecr.eu-central-1.amazonaws.com/sign-svc:arm64 .
docker build --platform linux/amd64 --no-cache --progress plain -f Dockerfile -t 503110391064.dkr.ecr.eu-central-1.amazonaws.com/sign-svc:amd64 .
# echo ""
# docker buildx imagetools inspect sign-svc:amd64
# docker buildx imagetools inspect sign-svc:arm64
