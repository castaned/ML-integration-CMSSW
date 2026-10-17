# Procesamiento de NanoAOD y conversión a HDF5

El modo `open_data` procesa archivos NanoAOD accesibles en el sistema de archivos del clúster. Desde la raíz del repositorio, generar los YAML de procesamiento, conversión y entrenamiento. En este ejemplo las entradas están organizadas en `fondo/` y `senal/`. Definir la cuenta Slurm autorizada para el proyecto antes de ejecutar:

```bash
cd "$HOME/ML-integration-CMSSW"
export SLURM_ACCOUNT="TU_CUENTA_SLURM"
python scripts/setup_yuca_course.py \
  --data-root "$HOME/Open-Data/Data" \
  --workspace-root "$HOME/Open-Data" \
  --account "$SLURM_ACCOUNT"
```

Se crean en `$HOME/Open-Data/configs/` las configuraciones para procesamiento, conversion, MLP y autoencoder. El generador **no sobrescribe** YAML existentes; `--force` solo debe usarse deliberadamente. Comprueba que las rutas y el ID `2=fondo`, `1=senal` son correctos:

```bash
python - <<'PY'
from pathlib import Path
import yaml

base = Path.home() / "Open-Data/configs"
for name in ("data_processing_config.yaml", "root2h5_config.yaml",
             "ml_model_config.yaml", "autoencoder_model_config.yaml"):
    with open(base / name) as handle:
        print(name, list(yaml.safe_load(handle)))
PY
```

## Procesar NanoAOD

Preparar las dependencias como se indica en [Entorno y configuración](01_entorno.md). La ruta de conda utilizada abajo corresponde al ejemplo de instalación en Yuca; adaptarla al clúster utilizado. `CONDA_SETUP_SCRIPT` permite a los nodos de Slurm activar el mismo entorno.

```bash
export CONDA_SETUP_SCRIPT=/apps/miniconda3/etc/profile.d/conda.sh
cd "$HOME/ML-integration-CMSSW/data_processing"
python execute_data_processing.py -f "$HOME/Open-Data/configs/data_processing_config.yaml"
squeue -u "$USER"
```

El YAML incorpora en `slurm_params.account` la cuenta indicada al generar las configuraciones; no hace falta volver a enviar manualmente con `sbatch -A`. Si el envio falla, consulta [Problemas frecuentes](06_problemas.md). Para consultar un ID concreto, usa `sacct -j ID --format=JobID,State,ExitCode` y revisa `logs/job_ID_*.err`.

Comprueba los ROOT producidos:

```bash
python - <<'PY'
from pathlib import Path
import uproot

base = Path.home() / "Open-Data/Processed/root"
for name in ("fondo", "senal"):
    files = sorted((base / name).glob("*.root"))
    assert files, f"Sin salida para {name}"
    for path in files:
        with uproot.open(path) as source:
            tree = source["Events"]
            print(name, path.name, tree.num_entries, "eventos")
            print("  W_pass:", int(tree["W_pass"].array(library="np").sum()))
PY
```

## Convertir a HDF5

```bash
cd "$HOME/ML-integration-CMSSW/data_processing/convert_h5"
python execute_convert_root2h5.py -f "$HOME/Open-Data/configs/root2h5_config.yaml"
squeue -u "$USER"
```

Verifica que cada HDF5 tenga las etiquetas correctas y el mismo numero de filas que su ROOT:

```bash
python - <<'PY'
from pathlib import Path
import h5py
import numpy as np

base = Path.home() / "Open-Data/Processed/h5"
for name, expected in (("fondo", 2), ("senal", 1)):
    files = sorted((base / name).glob("*.h5"))
    assert files, f"Sin HDF5 para {name}"
    for path in files:
        with h5py.File(path) as source:
            labels = source["Dataset_ID"][:]
            assert np.all(labels == expected)
            print(name, path.name, len(labels), "eventos")
PY
```

[Entrenamiento MLP](04_clasificador.md) · [Entrenamiento del autoencoder](05_autoencoder.md).
