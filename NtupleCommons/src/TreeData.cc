/*
 * TreeData.cc
 *
 *  Created on: May 23, 2017
 *      Author: hqu
 */

#include "DeepNTuples/NtupleCommons/interface/TreeData.h"

namespace deepntuples {

TreeData::TypeMap TreeData::type_names = []{
    TypeMap tmap;
    tmap[std::type_index(typeid(char))]                = "B";
    tmap[std::type_index(typeid(unsigned char))]       = "b";
    tmap[std::type_index(typeid(short))]               = "S";
    tmap[std::type_index(typeid(unsigned short))]      = "s";
    tmap[std::type_index(typeid(int))]                 = "I";
    tmap[std::type_index(typeid(unsigned int))]        = "i";
    tmap[std::type_index(typeid(float))]               = "F";
    tmap[std::type_index(typeid(double))]              = "D";
    tmap[std::type_index(typeid(long long))]           = "L";
    tmap[std::type_index(typeid(unsigned long long))]  = "l";
    tmap[std::type_index(typeid(bool))]                = "O";
    return tmap;
}();

} /* namespace deepntuples */
