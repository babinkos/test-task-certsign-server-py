#! /usr/bin/env bash
#pip list
pipenv run pip list
pipenv lock --pre
pipenv sync --dev
#pip list
pipenv run pip list
