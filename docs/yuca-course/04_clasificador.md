# 4. Clasificador MLP supervisado

El clasificador usa los HDF5 de ambas clases y transforma `Dataset_ID` con `class_id_map: {1: 1, 2: 0}`: senal es la clase positiva (`1`) y fondo la clase `0`. El YAML generado apunta a tus carpetas y al `mapping.json` del procesamiento.

Primero valida el lector:

```bash
cd "$HOME/ML-integration-CMSSW/ml_training"
python -m unittest discover -s tests -v
python - <<'PY'
from pathlib import Path
import yaml
from utilities.prepare import h5Dataset

with open(Path.home() / "Open-Data/configs/ml_model_config.yaml") as handle:
    data = yaml.safe_load(handle)["data"]
dataset = h5Dataset(data["input_paths"], data["features"], data["label"],
                    data["num_classes"], class_id_map=data["class_id_map"])
try:
    print("Eventos por archivo:", dataset.file_event_counts)
    print("Fondo:", dataset[0][1].item())
    print("Senal:", dataset[dataset.file_event_counts[0]][1].item())
finally:
    dataset.close()
PY
```

Esperamos fondo `0` y senal `1`. Para una primera prueba en CPU, usa Slurm en lugar de entrenar en el nodo de acceso:

```bash
mkdir -p logs
export CONDA_SETUP_SCRIPT=/apps/miniconda3/etc/profile.d/conda.sh
export CONDA_ENV_NAME=ml-open-data
export ML_CONFIG_PATH="$HOME/Open-Data/configs/ml_model_config.yaml"
job=$(sbatch --parsable -A p002 -p cpu -c 6 --mem=16G --time=04:00:00 \
  --job-name=cms_mlp --output=logs/job_%j.out --error=logs/job_%j.err \
  --export=ALL --wrap='bash run_training.sh')
echo "Trabajo: $job"
```

Tras terminar, revisa el ID real y los mensajes internos (no escribas la palabra literal `NUMERO`):

```bash
sacct -j "$job" --format=JobID,State,ExitCode
grep -E 'MLP training and optimization completed|MLP testing completed|\[ERROR\]' \
  "logs/job_${job}.out" "logs/job_${job}.err"
ls -lh "$HOME/Open-Data/Processed/results_mlp"/{best_model_*,ROC_*,cm_*}
```

El resultado incluye pesos `.pth`, un ONNX (conserva tambien su `.onnx.data` si aparece), curva ROC y matriz de confusion. Un `COMPLETED 0:0` de Slurm no reemplaza la revision del log y de los artefactos.

!!! warning "Interpretacion"
    El ejemplo divide eventos de los mismos archivos entre entrenamiento y prueba. La AUC describe esa prueba interna; no sustituye una muestra fisicamente independiente. Si el fondo es mucho mas abundante que la senal, la exactitud global puede ser engañosa: revisa la ROC, la matriz de confusion y las eficiencias por clase.

Continua en [Autoencoder](05_autoencoder.md).
