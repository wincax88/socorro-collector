#!/bin/bash

./scripts/dotenv ./config/prod.env gunicorn --reload --bind "0.0.0.0:8000" collector.wsgi --log-file -
