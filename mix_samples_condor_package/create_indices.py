import ROOT
import sys
import random

def get_event_keys(file_list):
    chain = ROOT.TChain("Events")
    for fname in file_list:
        chain.Add(fname)
    
    df = ROOT.RDataFrame(chain)
    return list(df.AsNumpy(columns=["Dataset_ID", "event"]).items())

def main():
    if len(sys.argv) < 3:
        print("Usage: create_indices.py <output_file> <txt_file1> [<txt_file2> ...]")
        sys.exit(1)

    output_file = sys.argv[1]
    txt_files = sys.argv[2:]

    root_files = []
    for txt in txt_files:
        with open(txt) as f:
            root_files += [line.strip() for line in f if line.strip().endswith(".root")]

    df = ROOT.RDataFrame("Events", root_files)
    data = df.AsNumpy(columns=["Dataset_ID", "event"])

    pairs = list(zip(data["Dataset_ID"], data["event"]))
    random.shuffle(pairs)

    with open(output_file, "w") as out:
        for dsid, evt in pairs:
            out.write(f"{int(dsid)} {int(evt)}\n")

if __name__ == "__main__":
    main()


