#!/bin/bash

container_name="openapi-to-pm"
docker exec ${container_name} /bin/bash -c "cd /usr/src/app && pytest"