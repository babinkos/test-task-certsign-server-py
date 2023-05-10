#! /usr/bin/env bash
mkdir -p ./certs
cd ./certs
openssl genrsa 4096 > privatekey.pem
openssl req -new -key privatekey.pem -out csr.pem
openssl x509 -req -days 30 -in csr.pem -signkey privatekey.pem -out public.crt
