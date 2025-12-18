# System architecture and workflow

The framework is organized around a pipeline that transforms CMS experimental data into trained machine learning models The following diagram illustrates the complete data flow:

![System architecture](../assets/images/vis_framework_eng.png)

The workflow begins with datasets stored in the CMS data storage, particularly focusing on the NanoAOD data format, which consists of a Ntuple-like, analysis-ready format containing selected physics objects and event information. More information [The CMS NanoAOD data tier](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookNanoAOD#NanoAOD_format).

The process unfolds in the following stages:

* **Data retrieval and filtering**: The first stage involves retrieving NanoAOD files from the distributed CMS data infrastructure (the GRID), applying user-defined filtering or skimming scripts to select relevant events and physics objects, and preparing the data for further processing.

* **Format conversion**: The filtered ROOT files (the native data format used in high-energy physics) are transformed into HDF5 files. The HDF5 format integrates seamlessly with modern Python-based machine learning frameworks such as TensorFlow, PyTorch, and scikit-learn. PyTorch is the framework used in the framework. This step is separated form the rest to allow for the transformation of ROOT files, even if they were not processed in the last stage.

* **Model training**: The HDF5 files serve as input for the training stage, where machine learning models are developed, different hyperparameter configurations are tested, and performance metrics are evaluated and visualized.

* **Inference deployment**: The final stage involves applying the trained model to new data to make predictions or classifications.

The dashed red square in the diagram specifically highlights the training part, which is designed to run in different computing environments. While this documentation primarily focuses on execution within the LXPLUS ecosystem, the machine learning module can be executed on any cluster, server, or local machine

Throughout this documentation we work within the CMS ecosystem. The framework leverages CMSSW releases, which contain the necessary physics objects, algorithms, and packages requiered for the data processing part.

Before diving into the practical implementation, let's understand the essencial infrastructure and software by providing a comprehensive introduction to the key systems you will interact with throughout this workflow.