#!/bin/sh

current_dir=$PWD

cd $current_dir/

yarn install

echo "Frontend dependencies installed."

cd $current_dir/api

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

echo "Backend dependencies installed."

export FLASK_APP=api.py
export FLASK_DEBUG=1

echo "Starting Flask server."
flask run