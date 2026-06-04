#!/usr/bin/env bash

pushd oddilovy_zpevnik_i && ./convert.py && popd && pushd oddilovy_zpevnik_ii && ./convert.py && popd && pushd nas_zpevnik && ./convert.py && popd
