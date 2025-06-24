import ROOT
import sys
import random

def main():
    if len(sys.argv) < 3:
        print("Usage: create_indices.py <output_file> <txt_file1> [<txt_file2> ...]")
        sys.exit(1)

    output_file = sys.argv[1]
    txt_files = sys.argv[2:]

    # Collect all ROOT files from input txt files
    root_files = []
    for txt in txt_files:
        with open(txt) as f:
            root_files += [line.strip() for line in f if line.strip().endswith(".root")]

    df = ROOT.RDataFrame("Events", root_files)
    data = df.AsNumpy(columns=["Dataset_ID", "event"])

    pairs = list(zip(data["Dataset_ID"], data["event"]))
    print(f"Loaded {len(pairs)} (Dataset_ID, event) pairs")

    random.shuffle(pairs)

    with open(output_file, "w") as out:
        count_written = 0
        for dsid_evt in pairs:
            # Sanity check that we have exactly 2 values in the tuple
            if not isinstance(dsid_evt, (tuple, list)) or len(dsid_evt) != 2:
                continue
            dsid, evt = dsid_evt
            # Also check they can be cast to int safely
            try:
                dsid_int = int(dsid)
                evt_int = int(evt)
            except Exception:
                continue
            out.write(f"{dsid_int} {evt_int}\n")
            count_written += 1

    print(f"Wrote {count_written} valid pairs to {output_file}")

    print("Sample of first 5 pairs:")
    for dsid, evt in pairs[:5]:
        print(f"{int(dsid)} {int(evt)}")

if __name__ == "__main__":
    main()


