#!/usr/bin/env python2


from argparse import ArgumentParser
import os
import subprocess
import glob

import multiprocessing

print("This script is still experimental and not fully completed")

parser = ArgumentParser('merge samples')
parser.add_argument('nsamples')
parser.add_argument('outdir')
parser.add_argument('infiles', metavar='N', nargs='+',
                    help='sample list files')

args = parser.parse_args()

tmpfiles = glob.glob('/tmp/mergeParallel_*')
if len(tmpfiles):
    for f in tmpfiles:
        print 'Removing old temp file: %s' % f
        os.remove(f)

if not os.path.isdir(args.outdir):

    allins=''
    for l in args.infiles:
        allins+=' '+l
        
    os.system('createMergeList '+str(args.nsamples)+' '+args.outdir+' '+allins)
    
    
#read number of jobs
file=open(args.outdir+'/nentries','r')
nJobs=file.read()

listtoberun=[]
listsucc=[]

for j in range(int(nJobs)):
    
    if os.path.exists(args.outdir+'/'+str(j)+'.succ'):
        listsucc.append(j)
        continue
    
    listtoberun.append(j)

print('successful: ',listsucc)


def _run(jobid):
    cmd = 'merge %s %d' % (os.path.join(args.outdir, 'mergeconfig'), jobid)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.communicate()[0]
#     print out
    if p.returncode == 0:
        print 'Job %d: Success!' % jobid
        return True
    else:
        print 'Job %d: Failed!' % jobid
        return False


n_threads = int(multiprocessing.cpu_count() / 2)
print "n_threads =", n_threads
n_threads = 2
print "n_threads =", n_threads
pool = multiprocessing.Pool(n_threads)
results = pool.map(_run, listtoberun)

print 'Finished! %d/%d jobs succeeded!' % (sum(results), len(listtoberun))




