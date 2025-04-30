import ROOT, sys, os

def load_keys(chunk_id, chunk_size, index_file):
    with open(index_file) as f:
        lines = [line.strip().split() for line in f if line.strip()]
    start = chunk_id * chunk_size
    end = min(len(lines), (chunk_id + 1) * chunk_size)
    return set((int(dsid), int(evt)) for dsid, evt in lines[start:end])

def main():
    if len(sys.argv) < 6:
        print("Usage: process_chunk.py <chunk_id> <chunk_size> <output_path> <index_file> <txt_file1> [<txt_file2> ...]")
        sys.exit(1)

    chunk_id = int(sys.argv[1])
    chunk_size = int(sys.argv[2])
    output_path = sys.argv[3]
    index_file = sys.argv[4]
    sample_lists = sys.argv[5:]

    all_files = []
    for txt in sample_lists:
        with open(txt) as f:
            all_files += [line.strip() for line in f if line.strip().endswith(".root")]

    ROOT.ROOT.EnableImplicitMT()
    df = ROOT.RDataFrame("Events", all_files)

    keys = load_keys(chunk_id, chunk_size, index_file)

    # C++ filter function using unordered_set of pairs
    filter_code = """
        #include <unordered_set>
        #include <utility>

        struct pair_hash {
            template <class T1, class T2>
            std::size_t operator()(const std::pair<T1, T2>& p) const {
                return std::hash<T1>()(p.first) ^ std::hash<T2>()(p.second);
            }
        };

        std::unordered_set<std::pair<ULong64_t, ULong64_t>, pair_hash> key_set = {
            %s
        };

        bool is_selected(ULong64_t dsid, ULong64_t evt) {
            return key_set.count(std::make_pair(dsid, evt));
        }
    """ % ", ".join(f"(std::make_pair({dsid}ULL, {evt}ULL))" for dsid, evt in keys)

    ROOT.gInterpreter.Declare(filter_code)
    df_filtered = df.Filter("is_selected(Dataset_ID, event)", "Filtered Entries")

    output_file = os.path.join(output_path, f"ntuple_merged_{chunk_id+1}.root")
    df_filtered.Snapshot("Events", output_file)

if __name__ == "__main__":
    main()

