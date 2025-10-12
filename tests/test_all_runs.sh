#!/bin/bash

set -e

for dir in ./compose_files/valid_* ./compose_files/semivalid_* ; do

  echo "- testing $dir ----------------------------------"

  if [[ "$dir" != "./compose_files/valid_interactive_alpine_environment" \
  && "$dir" != "./compose_files/valid_interactive_pip_path" ]]; then
    cd "$dir"
    ./test.sh
    cd ../../
  else
      echo "interactive container. Skipping."
  fi

done