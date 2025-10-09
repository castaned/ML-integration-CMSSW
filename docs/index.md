# CMS Machine Learning Framework

This repository provides a framework for processing, training, and making inferences with machine learning models in the context of CMS experiments. The framework facilitates data preparation, model training, and evaluation to support ML-based analyses in high-energy physics.

## Features

- **NanoAOD Filtering**: Scripts for selecting relevant events and producing key physics variables.
- **Data Preparation**: Merging filtered NanoAOD samples and converting them into HDF5 format for efficient ML model training.
- **Model Training & Evaluation**: Training machine learning models and performing performance tests to assess their effectiveness in anomaly detection or other tasks.

## Diagram

![System architecture](assets/images/fig01-ML-flow.png)

This diagram illustrates the tool's structure. The data processing section uses the CMSSW and GRID systems, but the training section does not.
