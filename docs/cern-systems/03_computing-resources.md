# Computational resources

As I mentioned, LXPLUS is just a cluster of login nodes, the CPU intense calculations has to be done by the worker nodes. CERN provides several mechanisms to access powerful compute nodes:

* [SWAN](https://swan.docs.cern.ch/intro/what_is/) offers an interactive data analysis environment, with jupyter notebook interface, pre-configured with ROOT, Python, and other scientific computing tools. It is ideal for exploratory analysis, prototyping, and visualization.

* [SLURM](https://batchdocs.web.cern.ch/linuxhpc/index.html) (Simple Linux Utility for Resource Management) is a workload manager designed for multi-node, high-performance computing (HPC) environments. It excels at tightly-coupled parallel applications that span multiple servers.

* [HTCondor](https://htcondor.readthedocs.io/en/latest/users-manual/quick-start-guide.html) is a distributed High-Throughput Computing (HTC) system that matches user job[^1] requirements with available computational resources. The user requiere an amount of cpu, memory, disk, amongs other options, and HTCondor creates a virtual execution environment with the requiered specifications by aggregating resources from all the available computer servers across the CERN cluster. 

CERN documentation states that SLURM is dedicated to running multi-nodes jobs (*e.g.* MPI programs), and that HTConodr should be used otherwise. In our case, no programs run in multi-node jobs.

The following diagram illustrates how AFS, EOS, and HTCondor interact within the CERN ecosystem:

![Visual diagram of interaction of AFS, EOS, and HTCondor](assets/images/fig03-afs-eos-htcondor.png)

[^1]: In this context, a job refers to a user-defined computational task, or set of tasks, submitted to a cluster via a scheduler like SLURM or HTCondor.