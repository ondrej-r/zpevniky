#!/bin/bash

mkdir -p ./artifacts

./act push \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest \
  -P ubuntu-20.04=catthehacker/ubuntu:act-20.04 \
  --artifact-server-path ./artifacts \
  --container-architecture linux/amd64 \
  "$@"
