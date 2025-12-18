# Storage Systems

Upon successful log to LXPLUS, you are placed in your home directory within a distributed filesystem called AFS (Andrew File System), documentation in [openAFS](https://www.openafs.org/). Your AFS home directory follows this structure:

`/afs/cern.ch/user/<initial>/<username>`

Where `<initial>` is the first letter of your username and `<username> is your CERN login name. For example, if your `<username>` is *olopez*, your home directory will be:

`/afs/cern.ch/user/o/olopez`

This directory serves as your primary workspace for creating files, directories, and environement, submitting computational script for execution, etc.

!!! warning "IMPORTANT"
    In this directory we have two major constaints:

    * The disk space quota in AFS is **10GB** per home directory. While sufficient for code and small files, it is not possible to store CMS experimental data, which can rage from gigabytes to terabytes per dataset.
    * It is not permitted to run CPU-intensive proccesses for extended periods of time. Otherwise, the administrator will terminate the process. 

To address AFS limitations, CERN provides the EOS storage system, a high-performace, petabyte-scale storage system optimized for large data files, where the qouta is significantlyl higher (*e.g.*, 1 TB, though this may vary). Check [EOS quick tutorial for beginners](https://cern.service-now.com/service-portal?id=kb_article&n=KB0001998) to learn more. The difference between AFS and EOS is beyond the scope, but we will explain why we use one or the other when it is necessary. 

Throughout this documentation, we are going to work in the AFS directory, the environment, files, scripts, will be located here, while all experimental data files will be saved in EOS.

In addition to AFS and EOS, CERN relies heavily on CERNVM File System (CernVM-FS) for software distribution. CernVM-FS is a read-only, distributed filesystem designed to efficiently deliver experiment software, libraries, and runtime environments across the worldwide computing infrastructure. CMSSW releases, external dependencies, and experiment-wide software stacks are distributed via CVMFS. This allows users to access identical software environments on LXPLUS, worker nodes, and GRID sites without installing or maintaining local copies.

In practice, this means that while your code and configuration live in AFS, your large datasets reside in EOS, and the CMS software stack is transparently provided through CVMFS. Together, these three systems form the backbone of the CMS computing environment, enabling scalable, reproducible, and efficient data processing across the CERN ecosystem. More detailed information can be found in [CernVM-FS documentation](https://cvmfs.readthedocs.io/en/stable/).
