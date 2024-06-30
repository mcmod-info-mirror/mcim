#!/bin/sh

export PYENV_ROOT="/root/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
source <(pyenv init -)
python --version
python webapi.py