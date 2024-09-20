#!/bin/bash

set -xe

# Config poetry
sudo /usr/local/py-utils/bin/poetry self add "poetry-dynamic-versioning[plugin]==1.4.1"
poetry config virtualenvs.in-project true
[ -e .venv ] || poetry env use /usr/local/bin/python

# Completion
pipx install argcomplete
mkdir -p ~/.local/share/bash-completion/completions
echo 'eval "$(register-python-argcomplete pipx)"' > ~/.local/share/bash-completion/completions/pipx
echo 'eval "$(poetry completions bash)"' > ~/.local/share/bash-completion/completions/poetry

# Init project
make init
