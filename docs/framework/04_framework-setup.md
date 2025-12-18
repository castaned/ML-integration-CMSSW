# Framework setup

With data access credentials established, and data identified, you must now configure the CMSSW environment appropriate for your data, and clone the repository with the new framework.

## Setting up the CMSSW release

Identify the correct CMSSW release for your data. This information is provided in dataset documentation. Execute these commands in sequence:

```bash
cmsrel CMSSW_13_3_0
cd CMSSW_13_3_0/src
cmsenv
```

The first command create a directory with all the files in the framework. You will see many of directories inside `CMSSW_13_3_0/`, each one has its own function, but we will work just inside `src/` directory.

!!! warning "IMPORTANT"
    1. `cmsenv` needs to be executed every time you open a new terminal to activate the environment variables. You need to be inside `CMSSW_13_3_0/` directory.
        2. The data processing component documented here has been tested only with the `CMSSW_13_3_0` release. The training section is not affected.

!!! note "Resources"
    If you want to learn more about the CMSSW system, its structure, and commands, you can explore [Intro to CMSSW](https://cms-opendata-workshop.github.io/workshop2022-lesson-cmssw/) and [CMSSW SCRAM](https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideBuildFile).


## Repository

From within your CMSSW `src/` directory, clone the framework repository:

```bash
git clone https://github.com/castaned/ML-integration-CMSSW some_name
cd some_name
```

`some_name` is the directory name for the cloned repository. The repository contains two main directories:

* `data_processing/`: Tools for retrieving, filtering, and converting CMS data

* `ml_training/`: Tools for training machine learning models and performing inference.

* `example_files`: Example files used in the [Example of usage](../usage/01_usage.md#example-of-usage) section of this documentation.

These components are designed to function independently. If you work only requires data processing, you may safely remove the `ml_training/` directory.
