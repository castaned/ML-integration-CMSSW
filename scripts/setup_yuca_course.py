"""Create personal, reproducible Yuca configs without changing repository examples."""

import argparse
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]


def generate(data_root, workspace_root, account, conda_env, max_files, force=False):
    data_root = Path(data_root).expanduser().resolve()
    workspace_root = Path(workspace_root).expanduser().resolve()
    config_dir = workspace_root / "configs"
    outputs = {
        "processing": config_dir / "data_processing_config.yaml",
        "conversion": config_dir / "root2h5_config.yaml",
        "mlp": config_dir / "ml_model_config.yaml",
        "autoencoder": config_dir / "autoencoder_model_config.yaml",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not force:
        raise FileExistsError("Configs already exist (use --force only if overwriting is intended): " + ", ".join(existing))
    if not account.strip():
        raise ValueError("A Slurm project account is required")

    files = {}
    for name in ("fondo", "senal"):
        found = sorted((data_root / name).glob("*.root"))
        if not found:
            raise FileNotFoundError(f"No ROOT files in {data_root / name}")
        files[name] = found[:max_files] if max_files else found

    root_out = workspace_root / "Processed" / "root"
    h5_out = workspace_root / "Processed" / "h5"
    processing = {
        "proxy": {"generate": 0},
        "data_processing": {
            "input_mode": "open_data",
            "conda_env": conda_env,
            "scheduler": "slurm",
            "slurm_params": {"executable_file": "run_filter.sh", "account": account,
                             "cpus": 1, "gpus": 0, "mem": "4000M", "time": "04:00:00", "partition": "cpu"},
            "processing_script": "example_files/main_process/filterNanoAOD.py",
            "eos_output_dir": str(root_out),
            "datasets": [
                {"name": "fondo", "ID": 2, "files": [str(path) for path in files["fondo"]]},
                {"name": "senal", "ID": 1, "files": [str(path) for path in files["senal"]]},
            ],
        },
    }

    with open(REPO / "data_processing/convert_h5/root2h5_config.yaml", encoding="utf-8") as handle:
        conversion = yaml.safe_load(handle)
    conversion["convertion"].update({"conda_env": conda_env,
                                    "input_dirs": [str(root_out / name) for name in ("fondo", "senal")],
                                    "eos_output_dir": str(h5_out)})
    conversion["scheduler"] = "slurm"
    conversion["slurm_params"]["account"] = account

    with open(REPO / "ml_training/ml_model_config.yaml", encoding="utf-8") as handle:
        mlp = yaml.safe_load(handle)
    mlp["data"].update({"input_paths": [str(h5_out / name) for name in ("fondo", "senal")],
                        "output_path": str(workspace_root / "Processed" / "results_mlp"),
                        "label_mapping": str(REPO / "data_processing/mapping.json"),
                        "class_id_map": {1: 1, 2: 0}})

    with open(REPO / "ml_training/autoencoder_model_config.yaml", encoding="utf-8") as handle:
        autoencoder = yaml.safe_load(handle)
    autoencoder["data"].update({"normal_input_paths": [str(h5_out / "fondo")],
                                "anomaly_input_paths": [str(h5_out / "senal")],
                                "output_path": str(workspace_root / "Processed" / "results_autoencoder")})

    config_dir.mkdir(parents=True, exist_ok=True)
    for key, config in (("processing", processing), ("conversion", conversion),
                        ("mlp", mlp), ("autoencoder", autoencoder)):
        with open(outputs[key], "w", encoding="utf-8") as handle:
            yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
        print(outputs[key])
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, help="Directory containing fondo/ and senal/")
    parser.add_argument("--workspace-root", required=True, help="Personal outputs and configs directory")
    parser.add_argument("--account", required=True, help="Slurm project account, e.g. p002")
    parser.add_argument("--conda-env", default="ml-open-data")
    parser.add_argument("--max-files", type=int, default=1, help="Files per class (0 means all)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated configs")
    args = parser.parse_args()
    if args.max_files < 0:
        parser.error("--max-files cannot be negative")
    generate(args.data_root, args.workspace_root, args.account, args.conda_env, args.max_files, args.force)
