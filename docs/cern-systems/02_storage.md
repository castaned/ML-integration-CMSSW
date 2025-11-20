# Storage Systems (AFS/EOS)

Upon successful log to LXPLUS, you are placed in your home directory within a distributed filesystem called AFS (Andrew File System), documentation in [openAFS](https://www.openafs.org/. Your AFS home directory follows this structure:

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
