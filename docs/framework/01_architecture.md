# General architecture

The developed framework is organized into two main sections, which can be used independently depending on the user’s needs. The first section focuses on processing data from CERN experiments, while the second section is dedicated to the training and usage of machine learning models. Each part is designed to be modular, reproducible, and configurable through YAML configuration files, facilitating adoption by a wide range of users.

<figure markdown id="fig-arch">
  ![MLFlow UI](../assets/images/vis_framework_eng.png)
      <figcaption>
           Figure 1: Framework architecture and workflow.
      </figcaption>
</figure>

## Processing and preparation of experimental data

This section is responsible for accessing, processing, and converting official CMS experiment data stored on the GRID. All operations are carried out within the LXPLUS environment and using CMS tools, in particular CMSSW, which guarantees full compatibility with CMS data formats, conventions, and metadata.

### Access and initial processing of NanoAOD

At this stage, NanoAOD files stored on the GRID are read using standard CMS mechanisms such as XRootD and DAS. Once the appropriate file endpoint is obtained, the framework automatically generates the required jobs to be executed on compute nodes dedicated to intensive processing.

The system transfers the necessary execution environment to each node (scripts, configuration files, and the CMSSW environment) and processes events by applying user-defined filters, selection cuts, and transformations.

The output of this phase consists of processed ROOT files collected on EOS, ready to be converted into formats more suitable for machine learning applications.

### Conversion from ROOT to HDF5

In this step, the framework generates a new set of jobs that take as input the previously produced ROOT files and convert them into the HDF5 format. HDF5 is a standard format in Python-based machine learning workflows and is widely used in the scientific community.

Although NanoAOD variables are typically scalars or fixed-length arrays, some variables may contain arrays of variable length. In such cases, these arrays are converted into fixed-length representations. As illustrated in [Figure 1](#fig-arch), this stage represents the transition from a particle physics problem to a data science problem.

Each stage of the workflow is driven by a YAML configuration file in which the user specifies input and output paths, variables to be processed, computational resources, environment parameters, and other relevant settings.

While the ROOT-to-HDF5 conversion can, in principle, be performed independently of LXPLUS and CMSSW, the strong coupling to these environments in this section enables full automation of the process using a single YAML configuration file.

## Machine learning

The second section of the framework is dedicated to the development of binary or multiclass classification models based on neural networks, with the goal of identifying the most suitable architecture for a given problem. This phase was designed with portability and modularity as core requirements, such that training does not depend on LXPLUS-specific tools or on CMSSW.

Although the repository provides examples using HTCondor together with Apptainer on LXPLUS, the system is designed to run in any environment that provides Python, standard Python machine learning libraries (in particular PyTorch), and common scientific analysis tools such as NumPy and h5py.

The machine learning section can be decomposed into the following steps:

1. Workflow configuration.

2. Transform ans split the dataset into training, validation, and test sets.

3. Hyperparameter optimization.

4. Distributed execution (optional, when using a resource manager).

5. Saving the best trained model in the standard PyTorch format.

6. Generation of metrics and figures for performance evaluation.

7. Visualization and tracking of trained models using MLflow.

8. Model inference.

As in the previous section, the configuration is defined through a YAML file specifying input and output paths, target model performance, the number of models to be generated, whether the task is binary or multiclass classification, and other relevant parameters.

If the user chooses to run training through a resource manager, an additional file (such as an HTCondor or SLURM submission script) must be provided. Otherwise, the machine learning workflow can be executed directly using Python.


