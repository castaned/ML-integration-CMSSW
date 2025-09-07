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
