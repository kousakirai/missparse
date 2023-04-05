git clone git://github.com/yyuu/pyenv.git ~/.pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
source ~/.bash_profile
PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy
pipenv run python3 main.py