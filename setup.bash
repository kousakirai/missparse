sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install libgl1-mesa-dev -y
if [ -s ~/.pyenv ]; then
    git clone https://github.com/yyuu/pyenv.git ~/.pyenv
fi
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
source ~/.bash_profile
PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy
pipenv run python3 main.py