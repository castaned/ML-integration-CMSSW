"""Follow ATLAS epoch records from a Slurm log; no extra GPU resources required."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import time

import yaml


def epoch_records(text):
    """Ignore headers, partial lines, and final multi-line metric dictionaries."""
    rows = {}
    for line in text.splitlines():
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                continue
            required = ('epoch', 'train_loss', 'validation_loss', 'validation_auc')
            if not all(key in row for key in required):
                continue
            if any(not math.isfinite(float(row[key])) for key in required):
                continue
            if int(row['epoch']) < 1:
                continue
            rows[int(row['epoch'])] = row
        except (ValueError, TypeError):
            continue
    return [rows[key] for key in sorted(rows)]


def sparkline(values):
    """ASCII trace: higher symbols indicate higher loss, on a shared scale."""
    symbols = ' .:-=+*#%@'
    low, high = min(values), max(values)
    return ''.join(symbols[min(9, int(9 * (v-low)/(high-low)))]
                   if high > low else '=' for v in values)


def render(rows, maximum, metrics=None):
    if not rows:
        return ('Esperando la primera época completada...\n'
                'El trabajo puede estar en cola o preparando los datos.\n'
                'Ctrl+C cierra este visor; el entrenamiento sigue en Slurm.')
    last = rows[-1]
    epoch = int(last['epoch'])
    filled = min(30, int(30 * epoch / maximum))
    best = min(rows, key=lambda row: row['validation_loss'])
    lines = ['ATLAS Higgs Challenge | Seguimiento del entrenamiento',
             f"[{'#'*filled}{'-'*(30-filled)}] Época {epoch}/{maximum} (máximo)",
             f"Pérdida entrenamiento: {last['train_loss']:.5f}",
             f"Pérdida validación:    {last['validation_loss']:.5f}",
             f"AUC validación:       {last['validation_auc']:.5f}",
             f"Mejor pérdida de validación: época {int(best['epoch'])}"]
    recent = rows[-40:]
    # One common min/max for the two traces preserves their relative heights.
    both = [float(r['train_loss']) for r in recent] + [float(r['validation_loss']) for r in recent]
    trace = sparkline(both)
    lines += ['', 'Pérdidas por época (izquierda a derecha; alto = mayor pérdida)',
              'Entrenamiento |' + trace[:len(recent)] + '|',
              'Validación    |' + trace[len(recent):] + '|']
    if metrics is not None:
        lines += ['', f"Entrenamiento terminado. Modelo conservado: época {metrics['best_epoch']}.",
                  f"AUC: {metrics['roc_auc_unweighted']:.5f} | AMS interna: {metrics['ams_validation_tuned']:.4f}",
                  'La parada temprana puede finalizar antes del máximo de épocas.']
    else:
        lines += ['', 'Ctrl+C cierra este visor; el entrenamiento sigue en Slurm.',
                  'Si el avance se detiene, consulta el estado del trabajo y su log.']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f', '--config', required=True)
    parser.add_argument('--log', required=True, help='Slurm output for this same YAML/run')
    parser.add_argument('--once', action='store_true', help='Show one snapshot and exit')
    args = parser.parse_args()
    expand = lambda value: Path(os.path.expandvars(os.path.expanduser(str(value))))
    config = yaml.safe_load(expand(args.config).read_text())
    log = expand(args.log)
    metrics_path = expand(config['output']['directory']) / 'metrics.json'
    try:
        while True:
            rows = epoch_records(log.read_text(errors='replace')) if log.exists() else []
            metrics = None
            try:
                metrics = json.loads(metrics_path.read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            if sys.stdout.isatty() and not args.once:
                print('\033[2J\033[H', end='')
            print(render(rows, int(config['training']['epochs']), metrics), flush=True)
            if args.once or metrics is not None:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nVisor cerrado. El trabajo de Slurm no se cancela.')


if __name__ == '__main__':
    main()
