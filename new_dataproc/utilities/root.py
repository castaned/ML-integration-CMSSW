import uproot
import awkward as ak
import tables

def write_carray(array, h5file, name, group_path='/', **kwargs):
        h5file.create_carray(group_path, name, obj=array, createparents=True, **kwargs)

def pad_or_truncate(jagged_array, max_len):
    padded = ak.pad_none(jagged_array, max_len, clip=True)
    padded = ak.fill_none(padded, 0)
    
    np_array = ak.to_numpy(padded)
    
    return np_array

def root_to_h5(input_file, tree_name, branches, output_file, max_len=10):
    upfile = uproot.open(input_file)
    tree = upfile[tree_name]
    
    if branches == "all":
        branches = tree.keys()
        
    ak_arrays = tree.arrays(branches, library="ak")
        
    with tables.open_file(output_file, mode="w") as h5file:
        for name in branches:
            array = ak_arrays[name]
            
            if not isinstance(array.layout, ak.contents.ListOffsetArray):
                np_array = ak.to_numpy(array)
                write_carray(np_array, h5file, name=name)
                continue
            
            np_array = pad_or_truncate(array, max_len)  # shape [N, variable-length]
            write_carray(np_array, h5file, name=name)
            
                
