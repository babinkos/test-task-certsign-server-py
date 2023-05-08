#! /usr/bin/env bash
# docker build --no-cache --progress plain -f Dockerfile -t 503110391064.dkr.ecr.eu-central-1.amazonaws.com/sign-svc:latest .
docker buildx build --platform linux/amd64,linux/arm64 --push --no-cache --progress plain -f Dockerfile -t 503110391064.dkr.ecr.eu-central-1.amazonaws.com/sign-svc:latest .
echo ""
docker buildx imagetools inspect 503110391064.dkr.ecr.eu-central-1.amazonaws.com/sign-svc:latest
