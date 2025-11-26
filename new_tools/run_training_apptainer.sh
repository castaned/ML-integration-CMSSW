#!/bin/bash

apptainer run --bind /eos --bind $PWD:/workspace tool_container.sif /workspace/main.py -f /workspace/ml_model_config.yaml

xrdfs "${REDIRECTOR}" mkdir -p "${EOS_DIR}"
xrdcp -r "${RESULTS_DIR}" "${REDIRECTOR}/${EOS_DIR}/"
