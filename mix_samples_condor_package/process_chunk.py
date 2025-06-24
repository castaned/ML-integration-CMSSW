import ROOT
import os
import sys
from ctypes import CFUNCTYPE, c_bool, c_longlong

def main():
    if len(sys.argv) != 6:
        print("Usage: process_chunk.py <chunk_id> <chunk_size> <output_path> <index_file> <txt_files>")
        sys.exit(1)

    chunk_id = int(sys.argv[1])
    chunk_size = int(sys.argv[2])
    output_path = sys.argv[3]
    index_file = sys.argv[4]
    txt_files = sys.argv[5].split(",")

    print(f"Chunk ID: {chunk_id}")
    print(f"Chunk size: {chunk_size}")
    print(f"Output path: {output_path}")
    print(f"Index file: {index_file}")
    print(f"TXT input files: {txt_files}")

    # Collect all ROOT files from txt_files
    all_files = []
    for txt in txt_files:
        if not os.path.exists(txt):
            print(f"Warning: txt file '{txt}' does not exist!")
            continue
        with open(txt) as f:
            files = [line.strip() for line in f if line.strip().endswith(".root")]
            all_files.extend(files)

    print("Input ROOT files:")
    for f in all_files:
        print(f" - {f}")
        if not os.path.exists(f):
            print("   ❌ File not found!")
        else:
            size = os.path.getsize(f)
            print(f"   ✅ Exists, size: {size} bytes")

    # Load ROOT files into RDataFrame
    df = ROOT.RDataFrame("Events", all_files)

    # Read the index file and get indices for this chunk
    with open(index_file) as f:
        # Split by whitespace (space or tab), not commas
        all_indices = [line.strip().split() for line in f if line.strip()]
    chunk_indices = all_indices[chunk_id * chunk_size : (chunk_id + 1) * chunk_size]

    if not chunk_indices:
        print(f"No indices found for chunk {chunk_id}. Exiting.")
        return

    selected_ids = set((int(dsid), int(evt)) for dsid, evt in chunk_indices)
    print(f"Processing chunk {chunk_id}: {len(selected_ids)} events")

    # Define the selection function
    def is_selected(dsid, event):
        return (int(dsid), int(event)) in selected_ids

    # Declare it in ROOT interpreter
    ROOT.gInterpreter.Declare("""
    std::function<bool(Long64_t, Long64_t)> is_selected_func;
    bool is_selected(Long64_t dsid, Long64_t event) {
        return is_selected_func(dsid, event);
    }
    """)

    # Bind Python function to ROOT
    is_selected_func = CFUNCTYPE(c_bool, c_longlong, c_longlong)(is_selected)
    ROOT.is_selected_func = is_selected_func

    # Filter dataframe with our selection function
    df_filtered = df.Filter("is_selected(Dataset_ID, event)", "Filtered Entries")

    selected_entries = df_filtered.Count().GetValue()
    print(f"Selected entries after filtering: {selected_entries}")
    if selected_entries == 0:
        print("No entries match the selection. Exiting without writing output.")
        return

    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, f"ntuple_merged_{chunk_id + 1}.root")
    df_filtered.Snapshot("Events", output_file)
    print(f"Output written to: {output_file}")

if __name__ == "__main__":
    main()

