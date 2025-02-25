from CRABClient.UserUtilities import config

config = config()

config.General.requestName = 'NanoAOD_Reduction'
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True
config.General.transferLogs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'  # Dummy, required by CRAB
config.JobType.scriptExe = 'reduce_nanoaod.sh'
config.JobType.inputFiles = ['reduce_nanoaod.py','reduce_nanoaod.sh','PSet.py']  # Script de reduccion
config.JobType.outputFiles = ['output.root']  # Archivo reducido
#config.JobType.sendPythonFolder = True

config.Data.inputDataset = '/WprimeToWZToWlepZlep_narrow_M1000_TuneCP5_13TeV-madgraph-pythia8/RunIIAutumn18NanoAODv7-Nano02Apr2020_102X_upgrade2018_realistic_v21-v1/NANOAODSIM'  # Reemplaza con el dataset real
config.Data.splitting = 'Automatic'
config.Data.unitsPerJob = 1  # Nmero de archivos por job
config.Data.outLFNDirBase = '/store/user/castaned/NanoAOD_Reduction/'  # Cambia tu username
config.Data.publication = False

config.Site.storageSite = 'T3_CH_CERNBOX'  # Reemplaza con tu sitio T2
