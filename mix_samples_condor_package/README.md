# MixSamples Condor Setup

This package provides everything needed to run the `mixSamples.py` script with Condor, allowing each chunk of events to be processed in parallel on a batch system.

## Setup Instructions:

1. **Prepare your environment**: Ensure you have access to a Condor-enabled system and your proxy is valid (`voms-proxy-init`).
2. **Modify paths and arguments**:
    - In `submit_all.sh`, update `<num_chunks>` with the number of chunks you want to submit.
    - Update the arguments in `mixSamples.jdl` and `submit_all.sh` to specify the `max_events`, `output_dir`, and the ROOT file lists (`txt_file1`, etc.).
3. **Run the submission script**: To submit the jobs, run:

```bash
bash submit_all.sh
```

This will loop over all chunks and submit them as Condor jobs.

## Files:
- `mixSamples.py`: Python script to merge, shuffle, and split the ROOT files into chunks.
- `submit_all.sh`: Bash script to submit Condor jobs for each chunk.
- `mixSamples.jdl`: Condor job description file.
