#!/usr/bin/env bash

pushd zp-I && ./convert.py && popd && pushd zp-II && ./convert.py && popd
