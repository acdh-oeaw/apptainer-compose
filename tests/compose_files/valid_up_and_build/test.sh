#!/bin/bash

rm valid_up_and_build.sif valid_up_and_build.def

set -e

../../../apptainer_compose.py --verbose up
