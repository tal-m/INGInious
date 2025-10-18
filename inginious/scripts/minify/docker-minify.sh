#!/usr/bin/bash

# Unless you setup nonroot docker, you will need to run this as root.

export ING_UID=$(stat -c "%u" .)
export ING_GID=$(stat -c "%g" .)

docker compose run --rm minify 
