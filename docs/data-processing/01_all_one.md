# CMS Machine Learning Framework

## Overview and objectives

This repository provides a comprehensive framework for processing, training, and deploying machine learning models within the context of CMS (Compact Muon Solenoid) experiments at CERN (Conseil Européen pour la Recherche Nucléaire, or European Council for Nuclear Research in english). The framework facilitates data preparation, model training, and evaluation to support ML-based analyses in high-energy physics.

In this framework, the primary goal is to maximize accessibility for physisits who are not used to machine learning development, as well as for new users navigating the complaex CERN computing ecosystem, particularly LXPLUS (Linux Public Login User Service) and CMSSW (CMS SoftWare).

CERN documentation can be difficult to navigate without knowing where to begin. There are multiple websites with different pieces of information, some of which are duplicated, with certain versions beings newer than others. Therefore, this documentation aims to explain the basic concepts and provide references to the pages where we found useful information for implementing and usuing the entire workflow.

!!! info
    Some documentation requires authentication with CERN account to access.
    
## System architecture and workflow

The fraemwok is organized around a pipeline that transforms CMS experimental data into trained machine learning models The following diagram illustrates the complete data flow:

![System architecture](assets/images/fig01-ML-flow.png)

The workflow begins with datasets stored in the CMS data storage, particularly focusing on the NanoAOD data format, which consists of a Ntuple-like, analysis-ready format containing selected physics objects and event information. More information [The CMS NanoAOD data tier](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookNanoAOD#NanoAOD_format).

The process unfolds in the following stages:

* **Data retrieval and filtering**: The first stage involves retrieving NanoAOD files from the distributed CMS data infrastructure (the GRID), applying user-defined filtering or skimming scripts to select relevant events and physics objects, and preparing the data for further processing.

* **Format conversion**: The filtered ROOT files (the native data format used in high-energy physics) are transformed into HDF5 files. The HDF5 format integrates seamlessly with modern Python-based machine learning frameworks such as TensorFlow, PyTorch, and scikit-learn. PyTorch is the framework used in the framework. This step is separated form the rest to allow for the transformation of ROOT files, even if they were not processed in the last stage.

* **Model training**: The HDF5 files serve as input for the training stage, where machine learning models are developed, different hyperparameter configurations are tested, and performance metrics are evaluated and visualized.

* **Inference deployment**: The final stage involves applying the trained model to new data to make predictions or classifications.

The dashed red square in the diagram specifically highlights the training part, which is designed to run in different computing environments. While this documentation primarily focuses on execution within the LXPLUS ecosystem, we provide an example for runnning it on a different cluster [ACARUS section](somewhere).

Throughout this documentation we work within the CMS ecosystem. The framework leverages CMSSW releases, which contain the necessary physics objects, algorithms, and packages requiered for the data processing part.


## CERN computing environment

Before diving into the practical implementation, let's understand the essencial infrastructure and software by providing a comprehensive introduction to the key systems you will interact with throughout this workflow.

### LXPLUS

LXPLUS (Linux Public Login User Service) is the primary access point to the CERN computing cluster. This service shaped the login nodes used to interact with our files, directories, environment, and computational environment. from these login nodes, you submit the script to executed in the worker nodes where the actual processing occurs.

As the name suggests, LXPLUS operates on Linux-based system, in particular a Red Hat Enterprise Linux distribution. To establish a conneciton to LXPLULS, you need:
* A valid CERN user account
* SSH (Secure shell) client software

There are multiple SSH client options; for example, PuTTY, Bitvise, or the terminal either on either windows, mac, or linux. All methods require your CERN username and authentication credentials. More information in [The LXPLUS Service](https://lxplusdoc.web.cern.ch/). 

Upon connecting, You will be asked for your password and verification code. If you have not yet activated the two factor authentication (2FA) look up [Setting up 2FA using your Smartphone](https://cern.service-now.com/service-portal?id=kb_article&n=KB0006587). 

![LXPLUS log in](assets/images/fig02-lxplus-login.png)

### Storage Systems: AFS and EOS

Upon successful log to LXPLUS, you are placed in your home directory within a distributed filesystem called AFS (Andrew File System), documentation in [openAFS](https://www.openafs.org/. Your AFS home directory follows this structure:

`/afs/cern.ch/user/<initial>/<username>`

Where `<initial>` is the first letter of your username and `<username> is your CERN login name. For example, if your `<username>` is *olopez*, your home directory will be:

`/afs/cern.ch/user/o/olopez`

This directory serves as your primary workspace for creating files, directories, and environement, submitting computational jobs, etc.

!!! warning "IMPORTANT"
    In this directory we have two major constaints:
    * The disk space quota in AFS is **10GB** per home directory. While sufficient for code and small files, it is not possible to store CMS experimental data, which can rage from gigabytes to terabytes per dataset.
    * It is not permitted to run CPU-intensive proccesses for extended periods of time. Otherwise, the administrator will terminate the process. 

To address AFS limitations, CERN provides the EOS storage system, a high-performace, petabyte-scale storage system optimized for large data files, where the qouta is significantlyl higher (*e.g.*, 1 TB, though this may vary). Check [EOS quick tutorial for beginners](https://cern.service-now.com/service-portal?id=kb_article&n=KB0001998) to learn more. The difference between AFS and EOS is beyond the scope, but we will explain why we use one or the other when it is necessary. 

Throughout this documentation, we are going to work in the AFS directory, the environment, files, scripts, will be located here, while all experimental data files will be saved in EOS.

### Computational resources

As I mentioned, LXPLUS is just a cluster of login nodes, the CPU intense calculations has to be done by the worker nodes. CERN provides several mechanisms to access powerful compute nodes:

* [SWAN](https://swan.docs.cern.ch/intro/what_is/) offers an interactive data analysis environment, with jupyter notebook interface, pre-configured with ROOT, Python, and other scientific computing tools. It is ideal for exploratory analysis, prototyping, and visualization.

* [SLURM](https://batchdocs.web.cern.ch/linuxhpc/index.html) (Simple Linux Utility for Resource Management) is a workload manager designed for multi-node, high-performance computing (HPC) environments. It excels at tightly-coupled parallel applications that span multiple servers.

* [HTCondor](https://htcondor.readthedocs.io/en/latest/users-manual/quick-start-guide.html) is a distributed High-Throughput Computing (HTC) system that matches user job requirements with available computational resources. The user requiere an amount of cpu, memory, disk, amongs other options, and HTCondor creates a virtual execution environment with the requiered specifications by aggregating resources from all the available computer servers across the CERN cluster. 

CERN documentation states that SLURM is dedicated to running multi-nodes jobs (*e.g.* MPI programs), and that HTConodr should be used otherwise. In our case, no programs run in multi-node jobs.

The following diagram illustrates how AFS, EOS, and HTCondor interact within the CERN ecosystem:

![Visual diagram of interaction of AFS, EOS, and HTCondor](assets/images/fig03-afs-eos-htcondor.png)

### CMSSW

While you could work with just LXPLUS, AFS, EOS, and HTCondor, you would lack access to CMS-specific software tools. The CMS collaboration has developed the software framework called CMSSW that encapsulates event reconstruction algorithms, calibration and correction tools, physics object definitions, analysis modules and utilities, amongs others. . The CMMSW framework is mantained in different versions, according to data-taking perioids, simulation campaigns, and software improvements. Each version contains specific configurations, corrections, and algorithms appropriate for particular analyses. The framework uses a modular architecture where users build their analysis code within the CMSSW structure.

Normally, we set up the CMSSW in our AFS directory. It creates a directory with a defined structure where we can use modules like EDProducer, EDFilter, and EDAnalyzer (where user code is implemented); SCRAM (Source Configuration, Release, And Management), the CMS build program; Python-based configuration files that define data processing workflows; etc. For detailed CMSSW documentation, conslut: [CMSSW Application Framework](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookCMSSWFramework).

While the machine learning training and inference components of this framework can oprate independently of CMSSW, the data processing stage requires a proper CMSSW environment to access CMS data formats and tools.

These are the key CERN system components you need to know to follow this tutorial. There are more, some of which will be explained later when requiered. Now, let's begin with the data processing. 


## First steps

Before executing any code, you must complete three essential setup procedures: accesing LXPLUS, establishing data access credentials, locating CMS datasets, and setting your CMSSW environment.


### Step 1: Logging into LXPLUS

Establish a secure shell connection to the LXPLUS cluster using your CERN credentials. Exmaple using CLI (command line interface):

```bash
ssh username@lxplus.cern.ch
```

Upon successful connection, you will be placed in your AFS home directory.

### Step 2: Setting up GRID proxy for data access

CMS data is distributed across the Worldwide LHC Computing Grid (WLCG), a global network of computing centers. Accessing this data requires proper authenticaiton through a GRID certificate and proxy.

A GRID certificate is a digital credential that identifies you to the GRID. If you don’t have a GRID certificate, follow the instructions [here](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookStartingGrid#ObtainingCert). You need to generate the certificate and export it to the `~/.globus` directory in your LXPLUS user space, which is the standard location.

The GRID certificate alone cannot be used directly for data access. You must generate a VOMS (Virtual Organization Membership Service) proxy. The proxy is a short-lived credential derived from your certificate, which includes yout CMS Virtual Organization (VO) membership information and has a limited lifetime for security.

Execute the following command to generate a CMS specific proxy:

```bash
voms-proxy-init --voms cms --valid 192:00 --out $HOME/.globus/x509up_u$(id -u)
```

This command generates the proxy to be used with CMS data and sets its lifitime to 192 hours, if you do not specify this, it defaults to 12 hours, and 192 hours is the maximum allowed.

We store the proxy inside our home directory. If you do not specify the output, it is stored by default in the `/tmp/` directory. The `x509up_u$(id -u)` format is a naming convention that includes your user ID.

!!! warning "Important"
    When the proxy expires, you must regenerate it using the same command. If not, it will result in authentication failures.

Verify that the certificate was correctly generated. First, we need to tell the system where our proxy is located, as mentioned earlier, the default directory is `/tmp/`, and the system will not find it if we saved it elsewhere. Therefore, we export the actual location:

```bash
export X509_USER_PROXY=$HOME/.globus/x509up_u$(id -u)
```

This environment variable tells the data access tools where to find your autentication credentials. Add this line to your `~/.bashrc` file to make it permanent. The next command shows us if it is correctly configured and vaild:

```bash
voms-proxy-info --all
```

Check that the timeleft value shows sufficient remaining time before expiration.

### Step 3: Locating and understanding CMS datasets

#### Data formats

CERN has a complex data retrieval system composed of different softwares and data centers. In general, people of the experiments, *e.g.*, CMS colaborators, produce data format releases that contain information recorded by the detectors from LHC runs or generated by Monte Carlo (MC) simulations. Each release corresponds to a specific data-taking period, trigger configuration, or simulation campaign. These releases can be in formats such as RAW, RECO, AOD, MiniAOD, and NanoAOD. In particular, **NanoAOD** is the newest format, released in 2016, which stores data using ROOT TTree objects instead of CMSSW C++ object like MiniAOD or AOD. Therefore, it can be analyzed using ROOT and/or python libraries.

While the other formats contain very detailed information, they are also very large and cumbersone for analysis. NanoAOD retains the most commonly used information for analysis while dramatically reducing the data volume, and it is easier to work with becuase of its Ntuple-like format. Find more information about nanoAOD in [Exploring CMS nanoAOD](https://cms-opendata-workshop.github.io/workshop2024-lesson-exploring-cms-nanoaod/aio.html), [The CMS NanoAOD data tier](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookNanoAOD#NanoAOD_format), and [cms-nanoAOD](https://gitlab.cern.ch/cms-nanoAOD).

#### Using DAS to locate datasets

The **Data Aggregation System (DAS)** is the catalog that helps find the exact Logical File Names (LFNs) of the samples. It provides a unified interface to query dataset locations, metedata, and file liests acrros the distributed GRID. DAS has its own query language, and the dataset paths follow a defined structure convention:

`/PrimaryDataset/ProcessedDataset/DataTier/`

There are two way to use it, using the web interface, or using the command line in a cluster that has accessed. For example

* /ZGToLLG_01J_5f_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM

Where `ZGToLLG_01J_5f_TuneCP5_13TeV-amcatnloFXFX-pythia8` is the primary dataset, `RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1` is the processed dataset, and `NANOAODSIM` is the data tier. You can find more information about DAS in [Locating Data Samples](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookLocatingDataSamples).

#### XRootD protocol for data access

Once you identify the actual LFN of your desired samples, you use the XRootD protocol to access them. **XRootD** provides a redirector service (entry point) that automatically connects you to the optimal data center (end point) based on network proximity and file availability. The data is not downloaded; instead, it is read efficiently through the XRootD protocol and accessed directly from the LXPLUS cluster. For more details, see [Using Xrootd Service (AAA) for Remote Data Access](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookXrootdService).


### Step 4: Setting up the  CMSSW release

With data access credentials established, and data identified, you must now configure the CMSSW environment appropriate for your data.

Identify the correct CMSSW release for your data. This information is provided in dataset documentation. Execute these commands in sequence:

```bash
cmsrel CMSSW_13_3_0
cd CMSSW_13_3_0/src
cmsenv```

The first command create a directory with all the files in the framework. You will see many of directories inside `CMSSW_13_3_0/`, each one has its own function, but we will work just inside `src/` directory.

!!! warning "IMPORTANT"
    1. `cmsenv` needs to be executed every time you open a new terminal to activate the environment variables. You need to be inside `CMSSW_13_3_0/` directory.
        2. The data processing component documented here has been tested only with the `CMSSW_13_3_0` release. The training section is not affected.

!!! note "Resources"
    If you want to learn more about the CMSSW system, its structure, and commands, you can explore [Intro to CMSSW](https://cms-opendata-workshop.github.io/workshop2022-lesson-cmssw/) and [CMSSW SCRAM](https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideBuildFile).

## Data processing implementation

Having established the foundational infrastructure, we now examine the practical implementation of the data processing pipeline, providing a comprehensive walkthrough of the repository structre, configuration files, and execution procedures.

### Repository

From within your CMSSW `src/` directory, clone the framework repository:

```bash
git clone https://github.com/castaned/ML-integration-CMSSW some_name
cd some_name
```

`some_name` is the directory name for the cloned repository. The repository contains two main directories:

* `data_processing/`: Tools for retrieving, filtering, and converting CMS data

* `ML_processing`: Tools for training machine learning models and performing inference.

These components are designed to function independently. If you work only requires data processing, you may safely remove the `ML_processing` directory.

Navigate to the `data_processing` directory:

```bash
cd data_processing
```
