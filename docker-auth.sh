#! /usr/bin/env bash
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 503110391064.dkr.ecr.eu-central-1.amazonaws.com