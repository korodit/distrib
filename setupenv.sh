#!/bin/bash
export LC_ALL=C
pip install --user virtualenv
virtualenv venv
. venv/bin/activate
pip install Flask
deactivate