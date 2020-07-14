#!/bin/bash

app="mellomaths/openapi-to-pm"
docker build -t ${app} .

docker push ${app}
