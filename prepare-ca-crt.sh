#! /usr/bin/env bash
mkdir -p ./certs
openssl genrsa 8192 > privatekey.pem
openssl req -new -key privatekey.pem -out csr.pem
openssl x509 -req -days 365 -in csr.pem -signkey privatekey.pem -out public.crt