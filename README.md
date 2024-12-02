1. Set a recent CMSSW version

```bash
cmsrel CMSSW_13_3_0
cd CMSSW_13_3_0/src
cmsenv
```

2. Clone the repository  and compile 

```bash
git clone https://github.com/castaned/ML-integration-CMSSW
scram b -j 4
```

3. Samples to merge are located in datasets directory, use mergeSamples script to merge into single root files

```bash
mergeSamples.py [events per output file] [output dir] [path to the filelist produced in step 1]
```
e.g.,
```bash
export OUTDIR=/path/to/files/tobemerged/
export MERGEDIR=/path/to/files/merged/
mergeSamples.py 200000 ${MERGEDIR} ${OUTDIR}/signal.txt ${OUTDIR}/bkg.txt
```

2. Split into training and testing samples

```bash
export TRAINDIR=${MERGEDIR}/train
export TESTDIR=${MERGEDIR}/test
mkdir -p $TRAINDIR $TESTDIR
mv ${MERGEDIR}/ntuple_merged_[.0-8.].root ${TESTDIR}/
mv ${MERGEDIR}/ntuple_merged_*.root ${TRAINDIR}/
```


### Convert `ROOT` files to `HDF5` files using `uproot`


```bash
wget https://raw.githubusercontent.com/cms-opendata-analyses/HiggsToBBNtupleProducerTool/refs/heads/opendata_80X/NtupleAK8/scripts/convert-uproot-opendata.py

```

Then you can run
```bash
python convert-uproot-opendata.py [input file (.root)] [output file (.h5)]
```
e.g.,
```
python convert-uproot-opendata.py ${TRAINDIR}/ntuple_merged_10.root ${TRAINDIR}/ntuple_merged_10.h5
```
which produces `HDF5` files with different arrays for each output variable.

