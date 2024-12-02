/*
 * sorting_modules.h
 *
 *  Created on: 5 Mar 2017
 *      Author: jkiesele
 */

#ifndef NTUPLECOMMONS_INTERFACE_SORTING_MODULES_H_
#define NTUPLECOMMONS_INTERFACE_SORTING_MODULES_H_

#include <algorithm>
#include <cmath>
#include <vector>
#include <iostream>

namespace sorting{

/*
 * the std::sort function needs a strict ordering.
 * means if your_function(a,b) is true, than your_function(b,a) must be false for all a and b
 */

template<class T>
bool comparePt(T a, T b){
    if(!a)return true;
    if(!b)return false;
    return a->pt()<b->pt();
}


template <class T>
class sortingClass{
public:

    sortingClass():sortValA(0),sortValB(0),sortValC(0),t_(0){}

    sortingClass(const T& t, float sortA, float sortB=0, float sortC=0){
        t_=t;
        sortValA=sortA;
        sortValB=sortB;
        sortValC=sortC;
    }
    sortingClass(const sortingClass&rhs):
    sortValA(rhs.sortValA),sortValB(rhs.sortValB),sortValC(rhs.sortValC),t_(rhs.t_)
    {	}
    
    sortingClass& operator=(const sortingClass&rhs){
    	sortValA=(rhs.sortValA);
    	sortValB=(rhs.sortValB);
    	sortValC=(rhs.sortValC);
    	t_=(rhs.t_);
    	return *this;
    }

    const T& get()const{return t_;}

    enum compareResult{cmp_smaller,cmp_greater,cmp_invalid};

    static inline bool isPhysValue(const float& val){
        if (val!=val)return false;
        if (std::isinf(val)) return false;
        return true;
    }

    static inline compareResult compare(const sortingClass& a, const sortingClass& b,int validx=0){
        float vala=a.sortValA;
        float valb=b.sortValA;
        if(validx==1){
            vala=a.sortValB;
            valb=b.sortValB;
        }else if(validx==2){
            vala=a.sortValC;
            valb=b.sortValC;
        }
        if(isPhysValue(vala) && isPhysValue(valb) && valb!=vala){
            if(vala>valb) return cmp_greater;
            else return cmp_smaller;
        }
        if(isPhysValue(vala) && !isPhysValue(valb))
            return cmp_greater;
        if(!isPhysValue(vala) && isPhysValue(valb))
            return cmp_smaller;
        return cmp_invalid;
    }

    //hierarchical sort
    static bool compareByABC(const sortingClass& a, const sortingClass& b){

        compareResult tmpres=compare(a,b,0);
        if(tmpres==cmp_smaller) return true;
        if(tmpres==cmp_greater) return false;

        tmpres=compare(a,b,1);
        if(tmpres==cmp_smaller) return true;
        if(tmpres==cmp_greater) return false;

        tmpres=compare(a,b,2);
        if(tmpres==cmp_smaller) return true;
        if(tmpres==cmp_greater) return false;

        return false;

    }

    static bool compareByABCInv(const sortingClass& a, const sortingClass& b){
			return compareByABC(b,a);
    }

 //private:
    float sortValA,sortValB,sortValC;
    


    T t_;
};



std::vector<size_t> invertSortingVector(const std::vector<sortingClass<size_t> > & in);


template<class T>
bool compareDxy(T b, T a){
    if(!a && b)return true;
    if(!b && a)return false;
    if(!a && !b)return false;
    return a->dxy()<b->dxy();
}

template<class T>
bool compareDxyDxyErr(T b, T a){
    if(!a) return true;
    if(!b) return false;
    if(!a && !b)return false;

    float aerr=a->dxyError();
    float berr=b->dxyError();


    float asig=a->dxy()/aerr;
    float bsig=b->dxy()/berr;

    if(!std::isnormal(asig) && std::isnormal(bsig))
        return true;
    else if(!std::isnormal(bsig) && std::isnormal(asig))
        return false;
    else if(!std::isnormal(bsig) && !std::isnormal(asig))
        return false;

    return asig<bsig;
}


template<class T>
bool pfCCandSort(T b, T a){

    bool ret=false;

    if(!a) ret= true;
    else if(!b) ret= false;
    else if(!a && !b)ret= false;
    else{

        float aerr=a->dxyError();
        float berr=b->dxyError();


        float asig=a->dxy()/aerr;
        float bsig=b->dxy()/berr;

        if(std::isnormal(asig) && std::isnormal(bsig)){
            return asig<bsig;
        }
        else if(!std::isnormal(asig) && std::isnormal(bsig))
            return true;
        else if(!std::isnormal(bsig) && std::isnormal(asig))
            return false;
        else if(!std::isnormal(bsig) && !std::isnormal(asig)){





        }
    }
}


}
#endif /* DEEPNTUPLES_DEEPNTUPLIZER_INTERFACE_SORTING_MODULES_H_ */
