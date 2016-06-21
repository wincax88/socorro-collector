#!/bin/bash

gunicorn --reload --bind "0.0.0.0:8000" collector.wsgi --log-file -
