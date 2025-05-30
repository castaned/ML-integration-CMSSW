#!/bin/bash



for file in "$MERGEDIR"/*.root; do
    if [ -f "$file" ]; then
        h5file="${file%.root}.h5"
        echo "Converting $file to $h5file"
        convert-uproot-opendata_v2.py "$file" "$h5file"
    fi
done
