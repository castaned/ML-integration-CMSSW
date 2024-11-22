## Merge outputs (with random mixing of different samples)

1. First create the file list (in this case we only take up to 3 output ROOT files for each QCD or Hbb sample).

```bash
cd DeepNTuples/NtupleAK8/run
export OUTDIR=/path/to/files/
ls $OUTDIR > samples.txt
for i in `cat samples.txt`; 
 do cd ${OUTDIR}/${i}; 
 ls */*/*/output_*.root | head -3 > ${i}_max3files.txt;
 cd -; 
done
```

2. Merge the samples (with random mixing)

```bash
mergeSamples.py [events per output file] [output dir] [path to the filelist produced in step 1]
```
e.g.,
```bash
export MERGEDIR=/path/to/files/merged_max3files/
mergeSamples.py 200000 ${MERGEDIR} ${OUTDIR}/QCD_Pt_*/QCD_Pt_*max3files.txt ${OUTDIR}/Bulk*/Bulk*max3files.txt
```

3. Split into training and testing samples

```bash
export TRAINDIR=${MERGEDIR}/train
export TESTDIR=${MERGEDIR}/test
mkdir -p $TRAINDIR $TESTDIR
mv ${MERGEDIR}/ntuple_merged_[.0-8.].root ${TESTDIR}/
mv ${MERGEDIR}/ntuple_merged_*.root ${TRAINDIR}/
```

## Convert `ROOT` files to `HDF5` files using `uproot`

This step requires a more recent version of CMSSW.

```bash
cmsrel CMSSW_10_4_0
cd CMSSW_10_4_0/src/
cmsenv
wget https://raw.githubusercontent.com/cms-opendata-analyses/HiggsToBBNtupleProducerToo/opendata_80X/NtupleAK8/scripts/convert-uproot-opendata.py
```

Then you can run
```bash
python convert-uproot-opendata.py [input file (.root)] [output file (.h5)]
```
e.g.,
```
python convert-uproot-opendata.py ${TRAINDIR}/ntuple_merged_10.root ${TRAINDIR}/ntuple_merged_10.h5
```
which produces `HDF5` files with different arrays for each output variable. Note that during this conversion, only the information for up to 100 particle candidates, 60 tracks, and 5 secondary vertices are saved in flattened, zero-padded, fixed-length arrays.
