#! /usr/bin/env bash
# see : https://pipenv.pypa.io/en/latest/advanced/#pipenv-and-other-python-distributions
if [ "$CONDA_DEFAULT_ENV" == "base" ] ; then
    echo "Current conda env = base, please choose specific one and activate with : conda activate <env>"
    conda env list
else
    if [ "$(pip list | fgrep -c pipenv)" == 0 ] ; then
        pip install --user pipenv
        ll $(which python)
    else
        pip list | fgrep pipenv
    fi
    if ! pipenv --venv ; then
        ll $(which python)
        pipenv --python=$(which python) --site-packages
        ll $(pipenv --py)
    else
        pipenv --venv
        ll $(pipenv --py)
    fi
    # https://code.visualstudio.com/docs/python/environments#_environment-variable-definitions-file
    if [ -f .env ] ; then
        [ "$(fgrep -c PYTHONPATH .env)" == 0 ] && ( echo "" >> .env ; echo "PYTHONPATH=$(pipenv --py)" | tee -a .env )
    else
        echo "PYTHONPATH=$(pipenv --py)" | tee .env
    fi
    [ "$(fgrep -c CONDA_DEFAULT_ENV .env)" == 0 ] && ( echo "" >> .env ; echo "CONDA_DEFAULT_ENV=$CONDA_DEFAULT_ENV" | tee -a .env )
    echo "Restart VSCode to make .env file re-read to Python be listed in inerpreters list to choose manually"
fi
