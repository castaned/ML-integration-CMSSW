# Random sampling - Optional


1. **Prepare your environment**: Ensure you have access to a Condor-enabled system and your proxy is valid (`voms-proxy-init`).
2. **Prepare the list of random events**: python3 create_indices.py <output_file> <txt_file1> [<txt_file2> ...]
2. **Modify paths and arguments**:
    - In `submit_all.sh`, update `<num_chunks>` with the number of chunks you want to submit.
    - Update the arguments in `mixSamples.jdl` and `submit_all.sh` to specify the `max_events`, `output_dir`, and the ROOT file lists (`txt_file1`, etc.).
3. **Run the submission script**: To submit the jobs, run:

```bash
bash submit_all.sh
```
