import ROOT
import random
import argparse
import os
import math
import sys

def main():
    # Raw positional arguments
    if len(sys.argv) < 4:
        print("Usage: mixSamples.py <max_events> <output_dir> <txt_file1> [<txt_file2> ...]")
        sys.exit(1)

    # Parse positional arguments
    max_events = int(sys.argv[1])
    output_dir = sys.argv[2]
    sample_lists = sys.argv[3:]

    # ✅ Ensure output directory exists
    if not os.path.exists(output_dir):
        print(f"📁 Output directory does not exist. Creating: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

    # Enable multithreading
    ROOT.ROOT.EnableImplicitMT()

    # Configuration
    tree_name = "Events"
    random_seed = 12345

    # Read all ROOT files from provided .txt files
    all_root_files = []
    for txt_file in sample_lists:
        with open(txt_file, "r") as f:
            root_files = [line.strip() for line in f if line.strip().endswith(".root")]
            all_root_files.extend(root_files)

    if not all_root_files:
        print("❌ No ROOT files found. Check your .txt input files.")
        return

    # Shuffle file list
    random.seed(random_seed)
    random.shuffle(all_root_files)

    # Load all files into a TChain
    chain = ROOT.TChain(tree_name)
    for f in all_root_files:
        chain.Add(f)

    # Load into RDataFrame
    df = ROOT.RDataFrame(chain)

    # Shuffle events by assigning a random number and sorting
    df_random = df.Define("rand", "gRandom->Rndm()").Sort("rand")

    # Count total events after shuffling
    total_events = df_random.Count().GetValue()

    # Calculate number of chunks
    n_chunks = math.ceil(total_events / max_events)

    print(f"📦 Will write {total_events} mixed events into {n_chunks} output file(s).")

    # Write output files
    for i in range(n_chunks):
        start = i * max_events
        end = min(start + max_events, total_events)

        df_chunk = df_random.Range(start, end)
        output_file = os.path.join(output_dir, f"ntuple_merged_{i+1}.root")
        df_chunk.Snapshot(tree_name, output_file)

        print(f"✅ Wrote: {output_file} (events {start} to {end - 1})")

if __name__ == "__main__":
    main()




