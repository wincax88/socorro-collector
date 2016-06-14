#!/bin/bash

./scripts/dotenv prod.env gunicorn --reload --bind "0.0.0.0:8000" collector.wsgi --log-file -
