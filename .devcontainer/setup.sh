#!/bin/bash

set -xe
mkdir -p ~/.local/share/bash-completion/completions

# Config pipx
pipx install argcomplete
echo '. <(register-python-argcomplete pipx)' > ~/.local/share/bash-completion/completions/pipx

# Config poetry
pipx install poetry==2.2.1
poetry config virtualenvs.in-project true
echo '. <(poetry completions bash)' > ~/.local/share/bash-completion/completions/poetry

# Project
make init
