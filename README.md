### Mixing of datasets and converting from ROOT to HD5 (arrays) format


1. Log into LXPLUS server

```bash
ssh username@lxplus.cern.ch
```


2. Set a recent CMSSW version

```bash
cmsrel CMSSW_13_3_0
cd CMSSW_13_3_0/src
cmsenv
```

3. Clone the repository  and compile 

```bash
git clone https://github.com/castaned/ML-integration-CMSSW DeepNTuples
scram b -j 4
```

4. Samples to merge are located in datasets directory, use mergeSamples script to merge into single root files

```bash
mergeSamples.py [events per output file] [output dir] [path to the filelist produced in step 1]
```
e.g.,
```bash
cd DeepNTuples
export OUTDIR=$PWD/datasets 
export MERGEDIR=$PWD/output
mergeSamples.py 200000 ${MERGEDIR} ${OUTDIR}/signal.txt ${OUTDIR}/bkg.txt
```

5. Split into training and testing samples (e.g. separate from 10 files, 7 for training and the rest for test)

```bash
export TRAINDIR=${MERGEDIR}/train
export TESTDIR=${MERGEDIR}/test
mkdir -p $TRAINDIR $TESTDIR
mv ${MERGEDIR}/ntuple_merged_[.0-7.].root ${TRAINDIR}/
mv ${MERGEDIR}/ntuple_merged_*.root ${TESTDIR}/
```


### Convert `ROOT` files to `HDF5` files using `uproot`  (up to maximum 100 particles) 


Then you can run
```bash
convert-uproot-opendata.py [input file (.root)] [output file (.h5)]
```
e.g.,
```
convert-uproot-opendata.py ${TRAINDIR}/ntuple_merged_5.root ${TRAINDIR}/ntuple_merged_5.h5
```
which produces `HDF5` files with different arrays for each output variable.

