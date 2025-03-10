# Data Processing, Training and Inference famework 

This repository provides a framework for processing, training, and making inferences with machine learning models in the context of CMS experiments. It includes scripts for filtering NanoAOD files, merging data, converting to HDF5 format, and running inference with ONNX models.

## Setup Instructions
 

### Step 1. Log into LXPLUS server (CERN computers)

```bash
ssh username@lxplus.cern.ch
```

### Step 2. Set up the required CMSSW version

```bash
cmsrel CMSSW_13_3_0
cd CMSSW_13_3_0/src
cmsenv  
```

IMPORTANT cmsenv need to be executed every time you open new terminal

### Step 3. Clone the repository  and compile 

```bash
git clone https://github.com/castaned/ML-integration-CMSSW DeepNTuples
scram b -j 4
```


## DATA Processing


### Step 1: Set up GRID proxy for accessing files

Ensure you have a valid GRID certificate. If you don’t, follow the instructions [here](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookStartingGrid#ObtainingCert)

Generate the certificate and store it in the .globus directory:

IMPORTANT the command below  need to be executed every time you open new terminal


```bash
voms-proxy-init --voms cms --valid 192:00 --out $HOME/.globus/x509up_u$(id -u)
```

Verify the certificate is correctly generated:
```bash
voms-proxy-info --all
```

If the certificate is not located in .globus directory, the variable need to be set with the following command

```bash
export X509_USER_PROXY=/afs/cern.ch/user/u/username/.globus/x509up_u{id}
```

el {id} tiene que reemplazarse para cada usuario


### Step 2: Navigate to the directory for job submission

```bash
cd MyNanoAODTools/scripts/
```

### Step 3: Verify dataset and branch selections

- Check input datasets in datasets.yaml. For reference, use the DAS query tool [here](https://cmsweb.cern.ch/das/) 

- Ensure the branchsel.txt file lists the desired branches for the NanoAOD skimmed version to be produced.
  You can find a list of branches in original file [here](https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/home)


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



### Step 8: Create .txt files to merge sample 

Back to the main directory 

```bash
cd ../../

```

Use the SamplesToMerge.sh script to produce .txt in the corresponding EOS directory (change Path accordingly to your EOS area)


```bash
# Set the directory containing the sample folders
BASE_DIR="/eos/user/c/castaned/NanoAOD_Filtered"
```


### Step 9: Merge samples (randomly) and produce h5 files 

e.g.,
```bash
export MERGEDIR=$PWD/output

mergeSamples.py 200000 ${MERGEDIR} /eos/user/c/castaned/NanoAOD_Filtered/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8_Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2_NANOAODSIM.txt /eos/user/c/castaned/NanoAOD_Filtered/WprimeToWZToWlepZlep_narrow_M1000_TuneCP5_13TeV-madgraph-pythia8_RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1_NANOAODSIM.txt
```

Split into training and testing samples, first find how many merged files were generated

```bash
ls output/*.root | wc 
```

Try to separate 70% for traning, 15% test, 15% validation

```bash
export TRAINDIR=${MERGEDIR}/train
export TESTDIR=${MERGEDIR}/test
export VALDIR=${MERGEDIR}/val
mkdir -p $TRAINDIR $TESTDIR $VALDIR

# Move files numbered from 0 to 50
mv ${MERGEDIR}/ntuple_merged_{0..50}.root ${TRAINDIR}/

# Move files numbered from 51 to 60
mv ${MERGEDIR}/ntuple_merged_{51..60}.root ${TESTDIR}/

# Move the remaining files to validation directory
mv ${MERGEDIR}/ntuple_merged_*.root ${VALDIR}/
```

Convert from .root to h5 (for all directories)

e.g.,
```bash
for file in "$TRAINDIR"/*.root; do
    if [ -f "$file" ]; then
        h5file="${file%.root}.h5"
        echo "Converting $file to $h5file"
        convert-uproot-opendata.py "$file" "$h5file"
    fi
done
```
which produces `HDF5` files with different arrays for each output variable.





## Training


NEED TO CONNECT WITH PREVIOUS PROCESS (DATA PROCESSING)



## Inference

 Ensure to have the requied packages

- onnxruntime: For running the ONNX model.
- uproot: To read NanoAOD files in pure Python.
- numpy: For handling input arrays.

```bash
pip install onnxruntime uproot numpy
```

 Execute script 

```bash
python test_onnx_nanoaod.py
```

The functionalities are: 
- Opens a NanoAOD ROOT file using uproot.
- Extracts electron kinematic variables (pt, eta, phi, mass).
- Loops over each event and selects the first electron.
- Formats the data as an input array for the ONNX model.
- Runs the ONNX model on each event and prints the output.



