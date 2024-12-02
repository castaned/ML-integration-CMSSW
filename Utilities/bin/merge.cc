/*
 * merge.cc
 *
 *  Created on: 22 May 2017
 *      Author: jkiesele
 */


#include "TFile.h"

#include <dirent.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
#include <signal.h>
#include <execinfo.h>
#include "TDirectory.h"

#include "DeepNTuples/Utilities/interface/mergeDescriptor.h"

static bool debug=true;

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

void fillTree( mergeDescriptor descr,
        const size_t outfileindex

){


    const size_t vecindex=0;
    //forked part

    TString idxstring=""; //for testing
    idxstring+=outfileindex;
    gl_currentfailfile=descr.outpath+"/"+idxstring+".fail";
    //make sure the fail path is set before anything else

    TFile * fout= 0;
    TTree * outtree =0;


    std::vector<size_t> entriesperchain;
    size_t totalentries=0;
    std::vector<TChain* > chains = descr.createChains(entriesperchain,totalentries,true);

    descr.infiles.clear();//not needed anymore, safe some memory


    size_t outtreeentry=0;
    size_t alloutentries=0;
    std::vector<size_t> entryindices=descr.startentries.at(vecindex);


    TString outfilename="ntuple_merged_"+idxstring+".root";
    //goes in the indexed loop later
    //std::cout << "new output file " <<outfilename <<std::endl;


    TString temp=createTempName();
    tempoutfile=temp;
    fout= new TFile(temp,"RECREATE");

    TDirectory* tdir=fout->mkdir("deepntuplizer","deepntuplizer");
    tdir->cd();
    outtree = chains.at(0)->CloneTree(0);//new TTree("tree","tree");//

    if(debug){
        std::cout << "looping " << outfileindex << " starting from: ";
        for(const auto& e:entryindices){
            std::cout << e << " ";
        }
        std::cout << std::endl;
    }

    for(size_t i=0;i<descr.whichchain_perfile.at(vecindex).size();i++){

        if(debug){
            if(i<5)
                std::cout << descr.whichchain_perfile.at(vecindex).at(i) <<std::endl;
        }

        //associate the next entry randomly to one of the sources
        size_t treeindex=descr.whichchain_perfile.at(vecindex).at(i);

        chains.at(treeindex)->GetEntry(entryindices.at(treeindex));
        entryindices.at(treeindex)++;

        outtree->Fill();

        outtreeentry++;
        alloutentries++;

    }
    outtree->Write();
    //check file as ok
    fout->Close();

    //doesn't work with xrootd
    // delete fout;
    if(debug){
        std::cout << idxstring << " file success"<<std::endl;
    }
    int counter=0;
    while(!DirectoryExists(descr.outpath.Data())){
        sleep(1);
        counter++;
        if(counter>240){
            system(("rm -f "+tempoutfile).Data());
            system(("touch "+gl_currentfailfile).data());
            delete fout;
            std::cerr << "merge of "<<outfilename << " failed (eos write problem)" <<std::endl;
            exit(0);
        }
    }


    bool notok=true;
    counter=0;
    while(notok){
        system(("cp "+temp+" "+descr.outpath+"/"+outfilename));
        //check if file copied is ok
        TFile * f = new TFile(descr.outpath+"/"+outfilename,"READ");
        if(!f || f->IsZombie()){
            counter++;
            if(counter<20){ //try only a few times
                continue;

            }
            else{
                system(("rm -f "+temp).Data());
                system(("touch "+descr.outpath+"/"+idxstring+".fail").Data());
                exit(0);
            }
        }
        system(("rm -f "+temp).Data());
        break;
    }

    system(("touch "+descr.outpath+"/"+idxstring+".succ").Data());

    exit(0);

}

int main(int argc, char *argv[]){
    TString helpmessage="\n\
       run this program with:\n merge <mergeDescripter file> <file index to be merged>";

    std::cout << "WARNING, please clean up the /tmp/ directory (delete any /tmp/mergeSamples_* files) if the program was killed or did not end successfully"<<std::endl;


    if(argc<3 || argc>3){
        std::cout << helpmessage <<std::endl;
        return -1;
    }

    std::string mergefile=argv[1];
    size_t index=atoi(argv[2]);

    mergeDescriptor descr;
    descr.readFromFile(mergefile,(int)index);

    fillTree(descr,index);

}
