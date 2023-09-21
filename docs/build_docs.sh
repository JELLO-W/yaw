#!/bin/bash

sphinx-apidoc -o source ../yaw
sphinx-build -b html . _build

