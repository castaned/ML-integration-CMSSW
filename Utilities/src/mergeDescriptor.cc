/*
 * mergeDescriptor.cc
 *
 *  Created on: 22 May 2017
 *      Author: jkiesele
 */




#include <fstream>


#include <dirent.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>
#include "TROOT.h"

#include "DeepNTuples/NtupleCommons/interface/TreeWriter.h"

#include "DeepNTuples/Utilities/interface/mergeDescriptor.h"

//#include "DeepNTuples/NtupleAK8/interface/JetInfoFillerAK8.h"
//#include "DeepNTuples/NtupleAK8/interface/FatJetInfoFiller.h"
//#include "DeepNTuples/NtupleAK8/interface/PFCandidateFiller.h"
//#include "DeepNTuples/NtupleAK8/interface/TrackFiller.h"
//#include "DeepNTuples/NtupleAK8/interface/SVFiller.h"

using namespace deepntuples;

static bool debug=true;

TString createTempName(){
    TString tin ="/tmp/mergeParallel_XXXXXXXXX";
    char t[tin.Length()];
    strcpy(t, tin.Data());
    int f=mkstemp(t);
    //std::cout << t << std::endl;
    close(f);
    TString n(t);
    return n;
}

TString prependXRootD(const TString& path){

    return path; //not used
    TString full_path = realpath(path, NULL);
    if(full_path.BeginsWith("/eos/cms/")){
        TString append="root://eoscms.cern.ch//";
        TString s_remove="/eos/cms/";
        TString newpath (full_path(s_remove.Length(),full_path.Length()));
        newpath=append+newpath;
        return newpath;
    }
    else if(full_path.BeginsWith("/eos/uscms/")){
        TString append="root://cmseos.fnal.gov//";
        TString s_remove="/eos/uscms/";
        TString newpath (full_path(s_remove.Length(),full_path.Length()));
        newpath=append+newpath;
        return newpath;
    }
    return path;
}

void setPreCache(TChain* tree){
    return ; //don't do anything for now
    tree->SetCacheSize(100e6);//100MB precache (eos is slow) - but increases CPU a lot...
}

bool FileExists (const std::string& name) {
    struct stat buffer;
    return (stat (name.c_str(), &buffer) == 0);
}

bool DirectoryExists( const char* pzPath )
{
    if ( pzPath == NULL) return false;
    DIR *pDir;
    bool bExists = false;
    pDir = opendir (pzPath);
    if (pDir != NULL){
        bExists = true;
        (void) closedir (pDir);
    }
    return bExists;
}


void mergeDescriptor::writeToFile(std::string filename){
    std::ofstream file(filename);
    serializedWrite(whichchain_perfile,file);
    serializedWrite(infiles,file);
    serializedWrite(outpath,file);
    serializedWrite(fractions,file);
    serializedWrite(startentries,file);
    file.close();
}
void mergeDescriptor::readFromFile(std::string filename, int pickone){
    std::ifstream file(filename);
    if(pickone<0){
        serializedRead(whichchain_perfile,file);
        serializedRead(infiles,file);
        serializedRead(outpath,file);
        serializedRead(fractions,file);
        serializedRead(startentries,file);
    }
    else{
        whichchain_perfile=std::vector<std::vector<size_t> >(1,std::vector<size_t>());
        serializedReadFromVector(whichchain_perfile.at(0),file,(size_t)pickone);

        serializedRead(infiles,file);//not sorted per outfile

        serializedRead(outpath,file);
        serializedRead(fractions,file);

        startentries=std::vector<std::vector<size_t> >(1,std::vector<size_t> ());
        serializedReadFromVector(startentries.at(0),file,(size_t)pickone);
    }
    file.close();
}


std::vector<TChain* > mergeDescriptor::createChains(
        std::vector<size_t>& entriesperchain,
        size_t& totalentries, bool usexrootd){

    static int ntimescalled=0;

    if(debug){
        std::cout << "creating chains" <<std::endl;
    }

    if(branchinfos.size())
        for(auto& b: branchinfos)
            delete b;
    branchinfos.clear();
    entriesperchain=std::vector<size_t>(infiles.size(),0);

    //    branchinfos.push_back(new JetInfoFillerAK8());
    //    branchinfos.push_back(new FatJetInfoFiller());
    //    branchinfos.push_back(new PFCandidateFiller());
    //    branchinfos.push_back(new TrackFiller());
    //    branchinfos.push_back(new SVFiller());

    std::vector<TChain* > chains;
    std::vector<TreeWriter*> treewriters;
    for(size_t i=0;i<infiles.size();i++){
        TString chainname="";
        chainname+=i;
        chainname+="_";
        chainname+=ntimescalled;
        auto t = new TChain(chainname,chainname);
        chains.push_back(t); //to get ahead of root background lsiting problems...
        treewriters.push_back(new TreeWriter(t, chainname, true));
    }

    for(size_t i=0;i<infiles.size();i++){
        for(const auto& f:infiles.at(i)){
            TString xrootdedpath=f;
            if(usexrootd)
                xrootdedpath=prependXRootD(xrootdedpath);
            chains.at(i)->Add(xrootdedpath+"/Events");
        }
        for(auto& bi:branchinfos){
            bi->setIsRead();
            bi->initBranches(treewriters.at(i));
        }
        entriesperchain.at(i) = chains.at(i)->GetEntries();
        setPreCache(chains.at(i));
        totalentries+=entriesperchain.at(i);
    }
    ntimescalled++;
    return chains;
}
