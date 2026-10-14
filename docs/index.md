# CMS Machine Learning Framework Documentation

Welcome to a comprehensive documentation for CMS Machine Learning Framework,  an end-to-end pipeline designed to transform CMS experimental data into trained machine learning (ML) models for high-energy physics (HEP) analysis.

This framework automates the full workflow inside CERN's destributed computing ecosystem, minimizing the amount of ML expertise required.

The repository can be found in [ML-integration-CMSSW](https://github.com/castaned/ML-integration-CMSSW)
---

## What this Framework Provides

The framework enables physicists to:

- **Process** NanoAOD datasets from the CMS experiment using distributed computing
- **Transform** ROOT files into ML-ready HDF5 formats with custom filtering
- **Train** machine learning models with HEP data
- **Deploy** trained models for physics analysis inference

All within CERN's computing infrastructure, with minimal prior ML experience required.

---

## Quick Start Path

If you are new to CMS computing or ML, follow these steps:

1. **[System Overview](getting-started/01_overview.md)** - Understand the complete workflow and the architecture of the framework.
2. **[CERN Access Setup](cern-systems/01_lxplus.md)** - Configure LXPLUS access, VOMS/GRID certificates, and environment.
3. **[Dataset Processing](framework/04_framework-setup.md)** - Process your NanoAOD files.
4. **[ML Training](framework/03_ml.md)** - Train ML models using the prepared datasets.

## Critical Requirements

For the [Practical Machine Learning in HEP course on Yuca with Open Data](practical-ml-hep/index.md), a CERN account is not required. Use the Yuca access and shared data supplied by your instructor. The requirements below apply to the CERN infrastructure workflow.


!!! warning "Before You Begin"
    You **must** have:

    - Valid CERN computing account with LXPLUS access
    - Basic familiarity with Linux command line
    - Understanding of ROOT files
    - Python knowledge

## Who is this documentation for?

- CMS physicists performing ML-based analyses
- Students new to CMS computing
- Analysts needing a reproducible ML pipeline
- Anyone converting CMS datasets into ML-ready formats



## Practical Machine Learning in HEP

[Taller en Yuca: clasificación de Higgs y autoencoder CMS](practical-ml-hep/index.md). Miércoles tres horas y jueves una hora, con ejercicios y guía de preparación.
