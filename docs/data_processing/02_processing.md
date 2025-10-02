# Retrieve, skim, and convert data

### Step 4: Update necessary configuration files

- Modify submit_condor.py
  - change the proxy path  (from x509up_u29575 to x509up_u{id}") where the {id} according to the user file
  - EOS user directory (e.g., /eos/user/u/username instead of /eos/user/c/castaned) according CERN username

- Modify run_filter.sh: 

  - work folder (e.g., replace /afs/cern.ch/work/c/castaned/CMSSW_13_3_0/src with your path, for instance /afs/cern.ch/user/u/username).
  - EOS directory (e.g. replace EOS_DIR="/eos/user/c/castaned/NanoAOD_Filtered/${DATASET_FOLDER}" with  EOS_DIR="/eos/user/u/username/NanoAOD_Filtered/${DATASET_FOLDER}"


- create local directory for output

```bash
mkdir filteredNanoAOD
```

- Create directory in EOS to store output

```bash
mkdir /eos/user/u/username/NanoAOD_Filtered/
```


### Step 5: Submit the Condor jobs

```bash
python3 submit_condor.py
```

### Step 6: Monitor job progress

```bash
condor_q
```

### Step 7: Verify the output
Once the jobs complete, check the EOS directory to confirm the skimmed samples were created successfully.

After the jobs are finished a `json` file named `dataset_mapping.json` will be created with a mapping of all datasets to an integer number (this is used later to define labels in the training process)


### Step 8: Create .txt files to merge sample 

Back to the main directory 

```bash
cd ../../

```

Use the `SamplesToMerge.sh` script to produce .txt in the corresponding EOS directory (change Path accordingly to your EOS area)


```bash
# Set the directory containing the sample folders
BASE_DIR="/eos/user/c/castaned/NanoAOD_Filtered"
```

Execute the bash script

```bash
bash SamplesToMerge.sh
```


### Step 9: Merge samples randomly (optional) 

See random sampling - optional section


### Step 10: Produce h5 files 


Convert from .root to h5 (for all directories)

Make sure all the variables are included in the `other_branches` list, if this is not the case udpate the list 
if the list is updated the code need to be recompiled in `src` directory by the command `scram b -j8`

```bash
emacs -nw Utilities/scripts/convert-uproot-opendata_v2.py
```

check that the script runs in one file


```bash
convert-uproot-opendata_v2.py $MERGEDIR/ntuple_merged_10.root $MERGEDIR/ntuple_merged_10.h5
```

Loop over complete dataset in the same MERGEDIR directory

```bash
bash convert_root_to_h5.sh
```
which produces `HDF5` files.
