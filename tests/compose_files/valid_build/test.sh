#!/bin/bash

set -e

../../../apptainer_compose.py build
../../../apptainer_compose.py up
