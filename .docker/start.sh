#!/bin/bash

app="mellomaths/openapi-to-pm"
docker build -t ${app} .
docker run -d --publish 8000:8000 \
  --name=${app} \
  -v $PWD:/app ${app}
