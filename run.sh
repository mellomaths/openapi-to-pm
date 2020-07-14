#!/bin/bash

cd ./app
uvicorn main:app --reload --host 0.0.0.0 --port 80