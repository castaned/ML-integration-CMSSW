/*
 * mergeSamples.cc
 *
 *  Created on: 23 Feb 2017
 *      Author: jkiesele
 *
 *
 *  Executable to merge sample collections, e.g. QCD and ttbar
 *
 *  Notes:
 *    - should work on samples.txt outputs from check.py
 *    - other inputs: output directory, number of samples to be merged to (if not given, use first nsamples)
 *    - writes out root files and at the end a samples.txt file again
 *    - should work with an unlimited number of input collections
 *
 */

#include "TString.h"
#include "TFile.h"
#include "TChain.h"
#include "TTree.h"
#include <vector>
#include <stdexcept>
#include <iostream>
#include "TRandom3.h"
#include <libgen.h>
#include <string>
#include <fstream>
#include "TDirectory.h"
#include <libgen.h>
#include "TStyle.h"
#include "TLine.h"
#include <stdlib.h>

//for control plots
#include "TH1D.h"
#include "TCanvas.h"
#include <ctime>



#include <dirent.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
#include "TROOT.h"
#include <stdio.h>
#include "DeepNTuples/Utilities/interface/mergeDescriptor.h"







std::vector<TString> readSampleFile(const TString& file, const TString& addpath){
    std::string line;
    std::vector<TString>  out;
    std::ifstream myfile (file.Data());
    if (myfile.is_open()){
        while ( getline (myfile,line) ){
	  //            out.push_back(addpath+"/"+(TString)line);
            out.push_back((TString)line);
        }
        myfile.close();
    }
    else
        throw std::runtime_error("could not read file");
    return out;
}



mergeDescriptor prepareSplitting(const std::vector<std::vector<TString> >& infiles,
        const size_t entriesperfile,const TString& outpath){

    mergeDescriptor out;
    out.infiles=infiles;
    out.outpath=outpath;


    // input files read, create TChains
    std::vector<size_t> entriesperchain;
    size_t totalentries=0;
    std::vector<TChain* > chains = out.createChains(
            entriesperchain,totalentries);

    //std::cout << "setting up trees... \nPlease ignore wrong branch type errors - they do no harm." <<std::endl;
    //read in files




    //create "binning"
    out.fractions=std::vector<double>(chains.size());
    double alloldfracs=0;
    for(size_t i=0;i<out.fractions.size();i++){
        out.fractions.at(i) = (double)entriesperchain.at(i)/(double)totalentries + alloldfracs;
        alloldfracs=out.fractions.at(i);
    }

    std::cout << "entries per chain: ";

    for(const auto& e:entriesperchain)
        std::cout << e << " ";
    std::cout <<std::endl;
    for(const auto& e:entriesperchain){
        if(!e)
            throw std::runtime_error("at least one sample with zero contribution");
    }
    std::cout << "entry fractions: " ;
    for(const auto& e:out.fractions)
        std::cout << e << " ";
    std::cout <<std::endl;


    TRandom3 rand;


    std::vector<double> histobins(1,0);
    histobins.insert(histobins.end(),out.fractions.begin(),out.fractions.end());
    TH1D hist("samplefraction","samplefraction",histobins.size()-1,&histobins.at(0));
    std::vector<TH1D> contr_hists;
    for(size_t i=0;i<chains.size();i++){
        TString basen="";
        TH1D hcontr(basen,basen,500,0,totalentries);
        contr_hists.push_back(hcontr);
    }


    std::cout << "looping for indices" <<std::endl;
    std::vector<size_t> entryindices(chains.size(),0);

    size_t alloutentries=0;
    out.whichchain_perfile.clear();
    std::vector<size_t> perfiletmp;
    out.startentries.push_back(entryindices);
    while(1){

        size_t treeindex=std::lower_bound(out.fractions.begin(), out.fractions.end(),
                rand.Uniform(0,1))-out.fractions.begin();

        perfiletmp.push_back(treeindex);

        hist.Fill(histobins.at(treeindex));
        contr_hists.at(treeindex).Fill(alloutentries);

        entryindices.at(treeindex)++;
        if(entryindices.at(treeindex)>=entriesperchain.at(treeindex)){
            out.whichchain_perfile.push_back(perfiletmp);
            perfiletmp.clear();
            break;
        }

        if(perfiletmp.size()>=entriesperfile){
            out.whichchain_perfile.push_back(perfiletmp);
            perfiletmp.clear();
            out.startentries.push_back(entryindices);
        }
        alloutentries++;
        if(alloutentries>=totalentries){
            throw std::runtime_error("serious problem");
        }
    }
    std::cout << "prepared randomized indices" <<std::endl;


    TH1D fracs=hist;
    fracs.Scale(1./(double)totalentries);
    TCanvas cv;
    gStyle->SetOptStat(0);
    fracs.Draw();
    cv.Print(outpath+"/samplefractions.pdf");

    hist.Scale(1,"width");
    hist.Scale(1./(double)totalentries);
    hist.Draw();
    cv.Print(outpath+"/samplefractions_binwidth.pdf");


    double min=totalentries,max=0;
    for(const auto& h:contr_hists){
        double tmax=h.GetMaximum();
        double tmin=h.GetMinimum();
        if(tmax>max)max=tmax;
        if(tmin<min)min=tmin;
    }

    contr_hists.at(0).GetYaxis()->SetRangeUser(min*0.95,max*1.05);
    contr_hists.at(0).Draw("AXIS");
    contr_hists.at(0).GetYaxis()->SetRangeUser(min*0.95,max*1.05);

    for(size_t i=0;i<contr_hists.size();i++){
        int color=i+1;
        if(i>8)color+=30;
        contr_hists.at(i).SetLineColor(color);
        contr_hists.at(i).Draw("same");
    }
    cv.SetCanvasSize(cv.GetWindowWidth()*5,cv.GetWindowHeight());
    cv.SetLeftMargin(0.02);
    cv.SetRightMargin(0.02);
    double count=0;
    for(size_t i=0;i<totalentries/entriesperfile+1;i++){
        if(count){
            TLine * l = new TLine(count,min*0.95,count,max*1.05);
            l->SetLineColorAlpha(kBlack,0.5);
            l->Draw("same");
        }
        count+=entriesperfile;
    }
    cv.Print(outpath+"/sample_contributions.pdf");

    //launch make the children
    for(auto& c:chains)
        delete c; //clear before forking

    gROOT->Reset();//really annoying root behaviour with all the background globals
    return out;

}


#include <signal.h>
#include <execinfo.h>
std::string gl_currentfailfile="";
TString tempoutfile="";
void kill_callback_handler(int signum){
    system(("touch "+gl_currentfailfile).data());
    system(("rm -f "+tempoutfile).Data());
    exit(signum);
}
void segfault_callback_handler(int signum){
    system(("touch "+gl_currentfailfile).data());
    system(("rm -f "+tempoutfile).Data());


    const int lines=100;
    void *array[lines];
    size_t size;

    // get void*'s for all entries on the stack
    size = backtrace(array, lines);

    // print out all the frames to stderr
    fprintf(stderr, "Error: signal %d:\n", signum);
    backtrace_symbols_fd(array, size, STDERR_FILENO);
    exit(signum);
}


int main(int argc, char *argv[]){

    //simple opt parsing
    TString helpmessage="\n\
    run this program with:\n \
    <nEntriesPerFile (about 400k is a good choice)> <outputdir> <input sample.txt 0> <input sample.txt 1> <input sample.txt 2> ...\
             ";

    if(argc < 4 || atof(argv[1]) == 0){
        std::cout << helpmessage <<std::endl;
        return -1;
    }
    size_t entriesperfile=atof(argv[1]);
    const TString outpath=argv[2];

    //check if exists
    if(DirectoryExists(outpath.Data())){
        std::cout << "ERROR: output directory must not exists ("<<outpath << ")"<<std::endl;
        return -1;
    }


    system(("mkdir -p "+outpath).Data());

    std::vector<std::vector<TString> > infiles;

    // unsigned concurentThreadsSupported = std::thread::hardware_concurrency();
  //  int numCPU = sysconf(_SC_NPROCESSORS_ONLN);

   // size_t maxrunning=numCPU;

    for(int i=3;i<argc;i++){
        TString samplefile=argv[i];
        TString inpath=dirname(argv[i]);
        inpath+="/";
        infiles.push_back(readSampleFile(samplefile,inpath));
    }


    mergeDescriptor descr=prepareSplitting(infiles,
            entriesperfile,outpath);

    descr.writeToFile((outpath+"/mergeconfig").Data());
    std::ofstream file((outpath+"/nentries").Data());
    file << descr.startentries.size();
    file.close();

}








