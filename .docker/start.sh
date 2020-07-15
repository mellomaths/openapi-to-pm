#!/bin/bash

container_name="openapi-to-pm"
image_name="mellomaths/openapi-to-pm"
docker build -t ${image_name} .
docker run -d --publish 80:8000 \
  --name=${container_name} \
  -e ENV='development' \
  ${image_name}
