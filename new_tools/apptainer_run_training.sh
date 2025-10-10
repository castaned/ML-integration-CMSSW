#!/bin/bash

tar -xzvf data.tar.gz # --strip-components=1
apptainer run --bind $PWD:/workspace tool_container.sif /workspace/main.py -f /workspace/set_config_variables.txt
