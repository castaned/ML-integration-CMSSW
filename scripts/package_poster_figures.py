"""Zip actual poster figures on Yuca for download and sharing."""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=Path.home() / "Open-Data/Processed/results_autoencoder_dyjets_ht_10features/poster_figures")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    folder = args.folder.expanduser().resolve()
    output = (args.output or folder.parent / "graficos_poster_autoencoder_10variables.zip").expanduser().resolve()
    if not folder.is_dir():
        parser.error(f"Missing figure directory: {folder}")
    required = ["ROC_comparison.pdf", "scores_by_process.pdf", "architecture.pdf", "loss.pdf"]
    missing = [name for name in required if not (folder / name).is_file()]
    if missing:
        parser.error(f"Missing main poster figures: {missing}")
    files = sorted(path for path in folder.rglob("*") if path.is_file())
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, str(Path("poster_figures") / path.relative_to(folder)))
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
    print(f"ZIP verified: {output}\nFiles: {len(files)}")
