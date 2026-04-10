import argparse
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import uproot
import yaml


DEFAULT_COLORS = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#9467bd",
    "#ff7f0e",
    "#8c564b",
]


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def require_key(config, key):
    if key not in config:
        raise KeyError(f"Missing required key in config: '{key}'")
    return config[key]


def resolve_root_files(path_value):
    path = Path(path_value)
    if path.is_file() and path.suffix == ".root":
        return [path]
    if path.is_dir():
        return sorted(path.rglob("*.root"))
    raise FileNotFoundError(f"Input path does not exist or is not a ROOT file/directory: {path}")


def dataset_label(dataset_config, fallback_index):
    return dataset_config.get("label") or dataset_config.get("name") or f"dataset_{fallback_index}"


def collect_branch_names(plot_config):
    branch_names = {plot_config["branch"]}
    selection = plot_config.get("selection")
    if selection:
        tokens = (
            selection.replace("(", " ")
            .replace(")", " ")
            .replace(">", " ")
            .replace("<", " ")
            .replace("=", " ")
            .replace("!", " ")
            .replace("&", " ")
            .replace("|", " ")
            .replace("+", " ")
            .replace("-", " ")
            .replace("*", " ")
            .replace("/", " ")
        ).split()
        for token in tokens:
            if token.replace(".", "", 1).isdigit():
                continue
            if token in {"and", "or", "not"}:
                continue
            branch_names.add(token)
    return sorted(branch_names)


def evaluate_selection(selection, arrays):
    if not selection:
        first_key = next(iter(arrays))
        return np.ones(len(arrays[first_key]), dtype=bool)

    safe_locals = {name: np.asarray(values) for name, values in arrays.items()}
    safe_globals = {"__builtins__": {}, "np": np, "abs": np.abs}
    mask = eval(selection, safe_globals, safe_locals)
    return np.asarray(mask, dtype=bool)


def read_dataset_values(dataset_config, plot_config):
    tree_name = dataset_config.get("tree_name", "Events")
    files = resolve_root_files(require_key(dataset_config, "path"))
    if not files:
        raise FileNotFoundError(f"No ROOT files found for dataset path: {dataset_config['path']}")

    needed_branches = collect_branch_names(plot_config)
    values = []

    for root_file in files:
        with uproot.open(root_file) as handle:
            tree = handle[tree_name]
            arrays = tree.arrays(needed_branches, library="np")
            mask = evaluate_selection(plot_config.get("selection"), arrays)
            branch_values = np.asarray(arrays[plot_config["branch"]])[mask]
            branch_values = branch_values[np.isfinite(branch_values)]
            values.append(branch_values)

    if not values:
        return np.array([], dtype=float)

    return np.concatenate(values) if len(values) > 1 else values[0]


def build_histogram(data, bins, value_range):
    return np.histogram(data, bins=bins, range=value_range)


def plot_variable(plot_config, datasets, output_dir):
    fig, ax = plt.subplots(figsize=(9, 6))

    bins = plot_config.get("bins", 40)
    value_range = tuple(plot_config["range"]) if plot_config.get("range") else None
    density = plot_config.get("density", False)
    normalize = plot_config.get("normalize", False)
    branch = plot_config["branch"]

    for index, dataset in enumerate(datasets):
        values = read_dataset_values(dataset, plot_config)
        if values.size == 0:
            continue

        counts, edges = build_histogram(values, bins=bins, value_range=value_range)
        if normalize or density:
            total = counts.sum()
            if total > 0:
                counts = counts / total

        centers = 0.5 * (edges[:-1] + edges[1:])
        color = dataset.get("color", DEFAULT_COLORS[index % len(DEFAULT_COLORS)])
        label = dataset_label(dataset, index)

        ax.step(centers, counts, where="mid", linewidth=2, color=color, label=label)

    ax.set_title(plot_config.get("title", branch))
    ax.set_xlabel(plot_config.get("xlabel", branch))
    ax.set_ylabel(plot_config.get("ylabel", "Normalized events" if (normalize or density) else "Events"))
    ax.grid(True, alpha=0.25)
    if plot_config.get("logy", False):
        ax.set_yscale("log")
    if value_range:
        ax.set_xlim(value_range)
    ax.legend(frameon=False)
    fig.tight_layout()

    output_name = plot_config.get("output", f"{branch}.png")
    output_path = Path(output_dir) / output_name
    fig.savefig(output_path, dpi=180)
    if plot_config.get("save_pdf", False):
        fig.savefig(output_path.with_suffix(".pdf"))
    plt.close(fig)


def main(config_path):
    config = load_config(config_path)
    plotting = require_key(config, "plotting")
    datasets = require_key(plotting, "datasets")
    plots = require_key(plotting, "plots")
    output_dir = Path(require_key(plotting, "output_dir"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for plot_config in plots:
        plot_variable(plot_config, datasets, output_dir)

    print(f"Saved {len(plots)} plot(s) to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot skimmed ROOT ntuples produced by data_processing.")
    parser.add_argument("-f", "--file", required=True, help="Path to the plotting YAML configuration.")
    args = parser.parse_args()
    main(args.file)
