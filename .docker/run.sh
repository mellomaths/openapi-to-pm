#!/bin/bash

cd ./app
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app