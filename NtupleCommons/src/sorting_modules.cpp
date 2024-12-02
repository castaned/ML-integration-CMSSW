


#include "../interface/sorting_modules.h"
#include <iostream>
namespace sorting{

std::vector<size_t> invertSortingVector(const std::vector<sortingClass<size_t> > & in){
    size_t max=0;
    for(const auto& s:in){
        if(s.get()>max) max=s.get();
    }

    std::vector<size_t> out(max+1,0);
    for(size_t i=0;i<in.size();i++){
        out.at(in.at(i).get())=i;
    }
   // for(const auto& s:out){
   //     std::cout << s << std::endl;
   // }
   // std::cout << std::endl;
    return out;
}

}
