"""Prepare an unweighted DY HT pilot and matched five/ten-feature runs."""
import argparse
import copy
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
BINS = ("70to100", "100to200", "200to400", "400to600")
BASE_FEATURES = ["MET_pt", "M3l", "Z_deltaR", "Z_mass", "Lep_pt_sum"]
EXTRA_FEATURES = ["Z_pt", "Lep1Z_pt", "Lep2Z_pt", "Lep3W_pt", "W_mt"]


def generate(base, account=None):
    base = Path(base).expanduser().resolve()
    def load(name):
        return yaml.safe_load((base / name).read_text())
    processing = load("sm_cocktail_processing_config.yaml")
    conversion = load("sm_cocktail_root2h5_config.yaml")
    model = load("autoencoder_sm_cocktail_dy102_ptsum_config.yaml")
    targets = {"dyjets_ht_processing_config.yaml": processing,
               "dyjets_ht_root2h5_config.yaml": conversion}
    manifest = {}
    for ht in BINS:
        folder = base / "Data" / f"DYJets_HT{ht}"
        files = sorted(folder.glob("*.root"))
        if not files:
            raise FileNotFoundError(f"No ROOT files in {folder}")
        manifest[ht] = [str(f) for f in files]
    files = [f for group in manifest.values() for f in group]
    if len({Path(f).name for f in files}) != len(files):
        raise ValueError("Duplicate ROOT basenames across bins; rename copies before processing")
    root = base / "Processed/root_dyjets_ht"
    h5 = base / "Processed/h5_dyjets_ht"
    processing["proxy"]["generate"] = 0
    p = processing["data_processing"]
    p.update(input_mode="open_data", scheduler="slurm", conda_env="ml-open-data",
             datasets=[{"name": "DYJets", "ID": 4, "files": files}],
             eos_output_dir=str(root))
    conversion["scheduler"] = "slurm"
    c = conversion["convertion"]
    c.update(conda_env="ml-open-data", input_dirs=[str(root / "DYJets")],
             eos_output_dir=str(h5), skip_empty_trees=True)
    required = ["MET_pt", "MET_phi", "Dataset_ID"]
    for channel in "ABCD":
        required += [f"{channel}_{suffix}" for suffix in
                     ("pass", "Sum_mass", "Dr_Z", "Zmass", "Sum_pt", "ptZ",
                      "Lep1Z_pt", "Lep2Z_pt", "Lep3W_pt", "Lep3W_phi")]
    c["branches"] = list(dict.fromkeys(c["branches"] + required))
    if account:
        p["slurm_params"]["account"] = account
        conversion["slurm_params"]["account"] = account
    for count, features in ((5, BASE_FEATURES), (10, BASE_FEATURES + EXTRA_FEATURES)):
        config = copy.deepcopy(model)
        name = f"autoencoder_dyjets_ht_{count}features"
        config["data"].update(features=features, normal_input_paths=[
            str(h5 / "DYJets"),
            str(base / "Processed/h5_sm_cocktail/WZ"),
            str(base / "Processed/h5_sm_cocktail/ZZ")],
            output_path=str(base / "Processed" / f"results_{name}"))
        config["model"]["name"] = name
        targets[f"{name}_config.yaml"] = config
    manifest_path = base / "dyjets_ht_input_manifest.json"
    for path in [base / name for name in targets] + [manifest_path]:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    for name, config in targets.items():
        with (base / name).open("x") as handle:
            yaml.safe_dump(config, handle, sort_keys=False)
        print(base / name)
    with manifest_path.open("x") as handle:
        json.dump({"weighting": "Unweighted concatenation of HT bins, not physical DY rates",
                   "files_by_ht": manifest}, handle, indent=2)
    print(f"ROOT inputs: {len(files)}; Slurm account: {p['slurm_params']['account']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / "Open-Data")
    parser.add_argument("--account", default=None)
    args = parser.parse_args()
    generate(args.config_dir, args.account)
