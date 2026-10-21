"""Follow ATLAS epoch records from a Slurm log; no extra GPU resources required."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import time
import subprocess

import yaml
from atlas_runs import run_from_log


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


def loss_chart(rows, width=54, height=9):
    """Plot actual epoch losses together; T=train, V=validation, *=overlap."""
    chosen = rows if len(rows) <= width else [rows[round(i*(len(rows)-1)/(width-1))] for i in range(width)]
    values = [float(r[k]) for r in chosen for k in ('train_loss', 'validation_loss')]
    low, high = min(values), max(values)
    span = high-low or 1
    grid = [[' ']*width for _ in range(height)]
    for i, row in enumerate(chosen):
        x = round(i*(width-1)/max(1, len(chosen)-1))
        for key, mark in (('train_loss', 'T'), ('validation_loss', 'V')):
            y = min(height-1, max(0, round((high-float(row[key]))/span*(height-1))))
            grid[y][x] = '*' if grid[y][x] != ' ' else mark
    lines = ['PÉRDIDA | T: entrenamiento  V: validación  *: coinciden']
    for y, row in enumerate(grid):
        label = high-span*y/(height-1) if high > low else low
        lines.append(f'{label:7.4f} |' + ''.join(row))
    lines += ['        +' + '-'*width,
              f"         Época {int(rows[0]['epoch'])}".ljust(width) + f"{int(rows[-1]['epoch'])}"]
    return lines


def job_status(job_id):
    """Read scheduler state without submitting work; unavailable is not failure."""
    if not job_id:
        return '', ''
    for command in (['squeue', '-h', '-j', job_id, '-o', '%T|%R'],
                    ['sacct', '-n', '-X', '-j', job_id, '--format=State,ExitCode', '-P']):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=3)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().splitlines()[0].split('|')
                return parts[0].split()[0].rstrip('+'), parts[1] if len(parts) > 1 else ''
        except (OSError, subprocess.TimeoutExpired):
            continue
    return '', ''


def render(rows, maximum, metrics=None, state='', detail='', log_text=''):
    title = ['ATLAS Higgs Challenge | Seguimiento del entrenamiento', '='*66]
    names = {'PENDING': 'EN COLA', 'RUNNING': 'EN EJECUCIÓN', 'COMPLETED': 'TRABAJO FINALIZADO',
             'FAILED': 'FALLÓ', 'CANCELLED': 'CANCELADO', 'TIMEOUT': 'TIEMPO AGOTADO',
             'OUT_OF_MEMORY': 'MEMORIA AGOTADA', 'COMPLETING': 'FINALIZANDO'}
    if state:
        title += [f"Slurm: {names.get(state, state)}" + (f' | {detail}' if detail else '')]
    if not rows:
        if metrics is not None:
            return '\n'.join(title + ['Resultados disponibles.',
                f"Modelo conservado: época {metrics['best_epoch']}",
                f"AUC: {metrics['roc_auc_unweighted']:.5f}",
                'No hay épocas en este log. Comprueba que corresponde a la misma ejecución.'])
        lines = title + [f"[{'-'*30}] Sin épocas registradas / máximo {maximum}"]
        if state == 'PENDING':
            lines += ['Esperando asignación de recursos; el entrenamiento aún no comienza.']
        elif state == 'RUNNING':
            lines += ['Trabajo activo; aún no se ha completado la primera época.']
        elif state in ('FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'COMPLETED'):
            lines += ['No se registró ninguna época. Revisa las últimas líneas del log.']
        else:
            lines += ['Esperando la primera época completada...', 'Consulta Slurm para conocer el estado del trabajo.']
        if log_text.strip():
            lines += ['', 'Últimas líneas del registro:'] + log_text.splitlines()[-6:]
        lines += ['', 'Ctrl+C cierra este visor; el entrenamiento sigue en Slurm.']
        return '\n'.join(lines)
    last = rows[-1]
    epoch = int(last['epoch'])
    filled = min(30, int(30 * epoch / maximum))
    best = min(rows, key=lambda row: row['validation_loss'])
    lines = title + [
             f"[{'#'*filled}{'-'*(30-filled)}] Época {epoch}/{maximum} (máximo)",
             f"Pérdida entrenamiento: {last['train_loss']:.5f}",
             f"Pérdida validación:    {last['validation_loss']:.5f}",
             f"AUC validación:       {last['validation_auc']:.5f}",
             f"Mejor pérdida de validación: época {int(best['epoch'])}"]
    lines += [''] + loss_chart(rows)
    if metrics is not None:
        lines += ['', f"Entrenamiento terminado. Modelo conservado: época {metrics['best_epoch']}.",
                  f"AUC: {metrics['roc_auc_unweighted']:.5f}",
                  'La parada temprana puede finalizar antes del máximo de épocas.']
    else:
        lines += ['', 'Ctrl+C cierra este visor; el entrenamiento sigue en Slurm.',
                  'Si el avance se detiene, consulta el estado del trabajo y su log.']
        if state == 'COMPLETED':
            lines += ['Slurm terminó, pero metrics.json no está disponible. Revisa el log y la carpeta de salida.']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f', '--config', required=True)
    parser.add_argument('--log', required=True, help='Slurm output for this same YAML/run')
    parser.add_argument('--once', action='store_true', help='Show one snapshot and exit')
    parser.add_argument('--job-id', help='Slurm job number returned by sbatch')
    args = parser.parse_args()
    expand = lambda value: Path(os.path.expandvars(os.path.expanduser(str(value))))
    config = yaml.safe_load(expand(args.config).read_text())
    log = expand(args.log)
    base = expand(config['output']['directory'])
    state, detail, checked = '', '', 0
    try:
        while True:
            log_text = log.read_text(errors='replace') if log.exists() else ''
            rows = epoch_records(log_text)
            run_directory = run_from_log(log_text)
            # Legacy logs need actual epoch records before reading old flat results.
            metrics_path = ((run_directory or base) / 'metrics.json') if (run_directory or rows) else None
            if time.monotonic()-checked >= 5:
                state, detail = job_status(args.job_id)
                checked = time.monotonic()
            metrics = None
            try:
                metrics = json.loads(metrics_path.read_text()) if metrics_path else None
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            if sys.stdout.isatty() and not args.once:
                print('\033[2J\033[H', end='')
            print(render(rows, int(config['training']['epochs']), metrics, state, detail, log_text), flush=True)
            print(f'Log: {log}', flush=True)
            if run_directory:
                print(f'Resultados: {run_directory}', flush=True)
            if args.once or metrics is not None or state in ('FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'COMPLETED'):
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nVisor cerrado. El trabajo de Slurm no se cancela.')


if __name__ == '__main__':
    main()
