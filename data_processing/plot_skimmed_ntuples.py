import argparse
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import uproot
import yaml


DEFAULT_COLORS = [
    "#3f90da",
    "#ffa90e",
    "#bd1f01",
    "#94a4a2",
    "#832db6",
    "#a96b59",
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


def apply_cms_style(style_config):
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#1f2937",
            "axes.linewidth": 1.8,
            "axes.labelsize": style_config.get("label_size", 18),
            "axes.titlesize": style_config.get("title_size", 20),
            "xtick.labelsize": style_config.get("tick_size", 15),
            "ytick.labelsize": style_config.get("tick_size", 15),
            "xtick.major.size": 7,
            "ytick.major.size": 7,
            "xtick.major.width": 1.6,
            "ytick.major.width": 1.6,
            "legend.fontsize": style_config.get("legend_size", 14),
            "font.family": style_config.get("font_family", "DejaVu Sans"),
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


def draw_cms_label(ax, style_config):
    cms_label = style_config.get("cms_label", "CMS")
    extra_label = style_config.get("extra_label", "Preliminary")
    lumi_label = style_config.get("lumi_label", "")

    ax.text(
        0.0,
        1.03,
        cms_label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=style_config.get("cms_size", 20),
        fontweight="bold",
        color="#111827",
    )
    if extra_label:
        ax.text(
            0.12,
            1.03,
            extra_label,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=style_config.get("extra_size", 15),
            style="italic",
            color="#374151",
        )
    if lumi_label:
        ax.text(
            1.0,
            1.03,
            lumi_label,
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=style_config.get("lumi_size", 14),
            color="#374151",
        )


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", which="major", direction="in", top=False, right=False)


def plot_variable(plot_config, datasets, output_dir):
    style_config = plot_config.get("style", {})
    apply_cms_style(style_config)
    fig, ax = plt.subplots(figsize=tuple(style_config.get("figsize", [10, 7])))

    bins = plot_config.get("bins", 40)
    value_range = tuple(plot_config["range"]) if plot_config.get("range") else None
    density = plot_config.get("density", False)
    normalize = plot_config.get("normalize", True)
    branch = plot_config["branch"]
    line_width = style_config.get("line_width", 2.8)
    fill_alpha = style_config.get("fill_alpha", 0.15)

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

        ax.step(centers, counts, where="mid", linewidth=line_width, color=color, label=label)
        ax.fill_between(centers, counts, step="mid", alpha=fill_alpha, color=color)

    ax.set_title(plot_config.get("title", branch))
    ax.set_xlabel(plot_config.get("xlabel", branch))
    ax.set_ylabel(plot_config.get("ylabel", "Arbitrary units" if (normalize or density) else "Events"))
    ax.grid(True, axis="y", alpha=0.18, linewidth=1.0)
    if plot_config.get("logy", False):
        ax.set_yscale("log")
    if value_range:
        ax.set_xlim(value_range)
    style_axes(ax)
    draw_cms_label(ax, style_config)
    ax.legend(
        frameon=False,
        loc=style_config.get("legend_loc", "upper right"),
        ncol=style_config.get("legend_ncol", 1),
        handlelength=2.8,
    )
    fig.tight_layout(pad=1.3)

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
