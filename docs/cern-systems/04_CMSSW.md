# CMSSW framework

While you could work with just LXPLUS, AFS, EOS, and HTCondor, you would lack access to CMS-specific software tools. The CMS collaboration has developed the software framework called CMSSW that encapsulates event reconstruction algorithms, calibration and correction tools, physics object definitions, analysis modules and utilities, amongs others. . The CMMSW framework is mantained in different versions, according to data-taking perioids, simulation campaigns, and software improvements. Each version contains specific configurations, corrections, and algorithms appropriate for particular analyses. The framework uses a modular architecture where users build their analysis code within the CMSSW structure.

Normally, we set up the CMSSW in our AFS directory. It creates a directory with a defined structure where we can use modules like EDProducer, EDFilter, and EDAnalyzer (where user code is implemented); SCRAM (Source Configuration, Release, And Management), the CMS build program; Python-based configuration files that define data processing workflows; etc. For detailed CMSSW documentation, conslut: [CMSSW Application Framework](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookCMSSWFramework).

While the machine learning training and inference components of this framework can oprate independently of CMSSW, the data processing stage requires a proper CMSSW environment to access CMS data formats and tools.

These are the key CERN system components you need to know to follow this tutorial. There are more, some of which will be explained later when requiered. Now, let's begin with the data processing. 
