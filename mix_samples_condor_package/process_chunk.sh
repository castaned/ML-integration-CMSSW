#!/bin/bash

CHUNK_ID=$1
CHUNK_SIZE=$2
OUTPUT_DIR=$3
INDEX_FILE=$4
shift 4
TXT_FILES="$@"

python3 process_chunk.py $CHUNK_ID $CHUNK_SIZE $OUTPUT_DIR $INDEX_FILE $TXT_FILES

