#!/bin/bash
gunicorn -c conf/gunicorn_config.py --reload src.app.wsgi --timeout 120

