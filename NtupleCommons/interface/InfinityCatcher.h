
#ifndef NTUPLECOMMONS_INTERFACE_INFINITYCATCHER_H_
#define NTUPLECOMMONS_INTERFACE_INFINITYCATCHER_H_

#include <cmath>

namespace deepntuples {

inline float catchInfs(const float& in, float replace_value=0){
    if(std::isinf(in) || std::isnan(in))
      return replace_value;
    else if(in < -1e32 || in > 1e32)
      return replace_value;
    return in;
}

   inline float catchInfsAndBound(const float& in, const float& replace_value, const float& lowerbound, const float& upperbound, const float& offset=0., const bool& use_offsets = true){
    float withoutinfs=catchInfs(in,replace_value);
    if(withoutinfs+offset<lowerbound) return lowerbound;
    if(withoutinfs+offset>upperbound) return upperbound;
    if(use_offsets)
      withoutinfs+=offset;
    return withoutinfs;
}

} /* namespace deepntuples */

#endif /* NTUPLECOMMONS_INTERFACE_INFINITYCATCHER_H_ */
