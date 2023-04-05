git config --global url."https://".insteadOf git://
git clone git://github.com/yyuu/pyenv.git ~/.pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
source ~/.profile
PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy
pipenv run python3 main.py