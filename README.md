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


```bash
mergeSamples.py [events per output file] [output dir] [path to the filelist produced in step 1]
```

Make sure the EOS directory for merged samples exist (otherwise create)

```bash
mkdir /eos/user/c/castaned/MergedSamples
```

e.g.,
```bash
mergeSamples.py 200000 /eos/user/c/castaned/MergedSamples  /eos/user/c/castaned/NanoAOD_Filtered/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8_Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2_NANOAODSIM.txt /eos/user/c/castaned/NanoAOD_Filtered/WprimeToWZToWlepZlep_narrow_M1000_TuneCP5_13TeV-madgraph-pythia8_RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1_NANOAODSIM.txt
```

2. Split into training and testing samples (e.g. separate from 10 files, 7 for training and the rest for test)

```bash
export TRAINDIR=${MERGEDIR}/train
export TESTDIR=${MERGEDIR}/test
mkdir -p $TRAINDIR $TESTDIR
mv ${MERGEDIR}/ntuple_merged_[.0-7.].root ${TRAINDIR}/
mv ${MERGEDIR}/ntuple_merged_*.root ${TESTDIR}/
```


Then you can run


```bash
convert-uproot-opendata.py [input file (.root)] [output file (.h5)]
```
e.g.,
```
convert-uproot-opendata.py ${TRAINDIR}/ntuple_merged_5.root ${TRAINDIR}/ntuple_merged_5.h5
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



