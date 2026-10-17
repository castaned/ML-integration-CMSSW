# Entorno y configuración para Open Data

## Repositorio

```bash
cd "$HOME"
git clone --branch opendata_dev https://github.com/castaned/ML-integration-CMSSW.git
cd ML-integration-CMSSW
```

Si el repositorio ya existe, actualizar la rama con `git pull --ff-only origin opendata_dev` después de revisar los cambios locales.

## Dependencias

| Componente | Uso |
| --- | --- |
| ROOT y PyROOT | Procesamiento con `example_files/main_process/filterNanoAOD.py` |
| uproot, awkward y NumPy | Lectura y transformación de variables de los eventos |
| PyTables y h5py | Conversión y lectura HDF5 |
| PyYAML | Lectura de configuraciones |
| PyTorch, scikit-learn y matplotlib | Entrenamiento, evaluación y gráficos |
| ONNX y onnxscript | Exportación de modelos, cuando está habilitada |

Utilizar un entorno conda personal compatible con ROOT y con las bibliotecas de la instalación. PyTorch debe corresponder al dispositivo elegido: CPU, NVIDIA/CUDA o AMD/ROCm. El entorno y los módulos del clúster deben estar disponibles también en los nodos de ejecución.

En Yuca, el ejemplo técnico usa el entorno `ml-open-data` y el script de activación de conda de la institución:

```bash
source /apps/miniconda3/etc/profile.d/conda.sh
conda activate ml-open-data
export CONDA_SETUP_SCRIPT=/apps/miniconda3/etc/profile.d/conda.sh
```

Adaptar estas rutas al entorno instalado. El filtro NanoAOD predeterminado importa `ROOT`; un entorno que solo incluya uproot no es suficiente para ese filtro.

## Verificación de las dependencias

```bash
python - <<'CHECK'
import ROOT, uproot, awkward, numpy, tables, h5py, yaml
import torch, sklearn, matplotlib
print("ROOT:", ROOT.gROOT.GetVersion())
print("PyTorch:", torch.__version__)
CHECK
```

## Entradas y salidas

Los ejemplos utilizan `$HOME/Open-Data/Data/fondo/` y `$HOME/Open-Data/Data/senal/` como entradas y `$HOME/Open-Data/Processed/` como salida. Pueden utilizarse otras rutas, incluidas entradas compartidas, indicándolas al generar los YAML.

La cuenta Slurm debe ser una cuenta autorizada para el usuario. En los comandos de envío se representa mediante `SLURM_ACCOUNT`; en Yuca puede consultarse con `misproyectos`.

[Continuar: archivos NanoAOD](02_datos.md).
