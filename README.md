
# CMS Machine Learning Framework

This repository provides a framework for processing, training, and making inferences with machine learning models in the context of CMS experiments. The framework facilitates data preparation, model training, and evaluation to support ML-based analyses in high-energy physics.

## Features

- **NanoAOD Filtering**: Scripts for selecting relevant events and producing key physics variables.
- **Data Preparation**: Merging filtered NanoAOD samples and converting them into HDF5 format for efficient ML model training.
- **Model Training & Evaluation**: Training machine learning models and performing performance tests to assess their effectiveness in anomaly detection or other tasks.

 

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

IMPORTANT `cmsenv` need to be executed every time you open new terminal

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


### Step 9: Merge samples (randomly) 


Follow instructions (README) in mix_samples_condor_package


### Step 10: Merge samples (randomly) and produce h5 files 


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
which produces `HDF5` files 





## Training


NEED TO CONNECT WITH PREVIOUS PROCESS (DATA PROCESSING)

An example of how to use the h5 files to train an autoencoder network can be found in `training
/train_AEs_pytorch.ipynb`


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



