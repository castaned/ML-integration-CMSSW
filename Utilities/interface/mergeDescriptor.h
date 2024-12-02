/*
 * serialise.h
 *
 *  Created on: 22 May 2017
 *      Author: jkiesele
 */

#ifndef DEEPNTUPLES_DEEPNTUPLIZER_INTERFACE_MERGEDESCRIPTOR_H_
#define DEEPNTUPLES_DEEPNTUPLIZER_INTERFACE_MERGEDESCRIPTOR_H_

/*
 *
 * Just a small helper for simple serialisation of vectors (needed by the merging exec)
 * only for flat data types not containing pointers
 *
 */

#include <vector>
#include <string>
#include "TString.h"
#include "TChain.h"
#include "DeepNTuples/NtupleCommons/interface/NtupleBase.h"

template <class T, class U>
inline void serializedWrite(const T& in, U& saveFile){
    saveFile.write(reinterpret_cast<const char *>(&in), sizeof(in));
}
template <class T, class U>
inline void serializedRead(T& in, U& saveFile){
    saveFile.read(reinterpret_cast< char *>(&in), sizeof(in));
}


template <class T, class U>
inline void serializedWrite(const std::vector<T>& in, U& saveFile){
    size_t len=in.size();
    saveFile.write(reinterpret_cast<const char *>(&len), sizeof(len));
    for(size_t i=0;i<len;i++)
        serializedWrite(in.at(i),saveFile);
}

template <class T, class U>
inline void serializedRead(std::vector<T>& in, U& saveFile){
    size_t len=0;
    saveFile.read(reinterpret_cast< char *>(&len), sizeof(len));
    in.resize(len,T());
    for(size_t i=0;i<len;i++)
        serializedRead(in.at(i),saveFile);
}

template <class T, class U>
inline void serializedReadFromVector(T& in, U& saveFile,size_t index){
    size_t len=0;
    saveFile.read(reinterpret_cast< char *>(&len), sizeof(len));
    for(size_t i=0;i<len;i++){
        if(index==i)
            serializedRead(in,saveFile);
        else{
            T dummy;
            serializedRead(dummy,saveFile);
        }
    }
}


template <class U>
inline void serializedWrite(const TString& in, U& saveFile){
    if(in.Length()>65535)
        throw std::out_of_range("serializedWrite: strings are limited to uint16_t length");
    uint16_t len=in.Length();
    saveFile.write(reinterpret_cast<const char *>(&len), sizeof(len));
    saveFile.write(in.Data(), len);
}

template <class U>
inline void serializedRead(TString& in, U& saveFile){
    uint16_t len=0;
    saveFile.read( reinterpret_cast<char*>( &len ), sizeof(len) );
    in="";
    if(len > 0){
        char* buf = new char[len];
        saveFile.read( buf, len );
        in.Append(buf,len);
        delete[] buf;
    }
}


TString createTempName();

TString prependXRootD(const TString& path);

void setPreCache(TChain* tree);

bool FileExists (const std::string& name) ;

bool DirectoryExists( const char* pzPath );



class mergeDescriptor{
public:

    ~mergeDescriptor(){
        for(auto& c: branchinfos)
            delete c;
    }

    std::vector<std::vector<size_t> > whichchain_perfile;
    std::vector<std::vector<TString> > infiles;
    TString outpath;
    std::vector<double> fractions;
    std::vector<std::vector<size_t> >startentries;

    void writeToFile(std::string filename);
    void readFromFile(std::string filename, int pickone=-1);
    std::vector<TChain* >  createChains(
            std::vector<size_t>& entriesperchain,
            size_t& totalentries, bool usexrootd=false);

private:
    std::vector<deepntuples::NtupleBase*> branchinfos;

};



#endif /* DEEPNTUPLES_DEEPNTUPLIZER_INTERFACE_MERGEDESCRIPTOR_H_ */
