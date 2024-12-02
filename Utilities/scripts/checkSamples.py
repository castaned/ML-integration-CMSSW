import ROOT as rt
import glob
import os

rt.gROOT.SetBatch()
inDir = '/eos/uscms/store/group/lpchbb/deepdoubleb/phi_all/'


c = rt.TCanvas('c','c',500,400)
tchain = rt.TChain('Events')
for tfileName in glob.glob(inDir + '/*.root'):
    n = tfileName.split('.root')[0].split('_')[-1]
    print glob.glob(inDir + '/' + n + '.succ')
    if not glob.glob(inDir + '/' + n + '.succ'): continue
    #tfile = rt.TFile.Open('root://cmseos.fnal.gov/' + tfileName)
    tchain.Add('root://cmseos.fnal.gov/' + tfileName)
    #tree = tfile.Get('deepntuplizer/tree')
    #tree.Draw('fj_sdmass>>htemp(100,0,300)','fj_isH')
    #c.SaveAs('fj_sdmass_fj_isH_%s.png'%n)
    #tree.Draw('fj_pt>>htemp(100,0,3000)','fj_isH')
    #c.SaveAs('fj_pt_fj_isH_%s.png'%n)
tchain.Draw('fj_sdmass>>htemp(100,0,300)','fj_isH')
c.SaveAs('fj_sdmass_fj_isH.png')
tchain.Draw('fj_pt>>htemp(100,0,3000)','fj_isH') 
c.SaveAs('fj_pt_fj_isH.png')  
    
    
