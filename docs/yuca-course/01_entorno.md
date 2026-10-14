# Repositorio y entorno de trabajo

Antes de comenzar, completar por separado el [primer acceso y activación de 2FA](00_acceso.md). Los pasos siguientes se ejecutan dentro de una terminal de Yuca, por SSH o desde Open OnDemand, con la cuenta ya activada.

## Descargar el repositorio del curso

Una vez dentro de una terminal de Yuca, clonar la rama del curso:

```bash
cd "$HOME"
git clone --branch opendata_dev https://github.com/castaned/ML-integration-CMSSW.git
cd ML-integration-CMSSW
git branch --show-current
git status -sb
```

La rama debe ser `opendata_dev`. Si el repositorio ya existe, usa `git pull --ff-only origin opendata_dev` desde esa rama. Si `git status -sb` muestra cambios locales, revisalos antes de actualizar.

## Activar el entorno del curso

El instructor comunica el nombre del entorno disponible y la cuenta Slurm. **Si el entorno ya existe, activarlo; no recrearlo ni reinstalar PyTorch.**

```bash
source /apps/miniconda3/etc/profile.d/conda.sh
conda activate ml-open-data
mkdir -p "$HOME/hep-workshop/configs" "$HOME/hep-workshop/logs"
python -c "import pandas, sklearn, yaml, uproot, awkward, torch, h5py, onnx; print('Entorno del curso listo')"
```

Sustituir `ml-open-data` si el instructor proporciona otro nombre. Si falla un import, consultar al instructor antes de modificar un entorno compartido. Para los ejemplos preparados de Higgs y autoencoder no es necesario cargar PyROOT: los NanoAOD Higgs se leen con uproot.

## ROOT para el procesamiento del framework

Este paso corresponde al filtro NanoAOD original del framework y a su conversión a HDF5:

```bash
module load root/6.24.08
export PYTHONPATH="$(root-config --libdir):${PYTHONPATH:-}"
export CONDA_SETUP_SCRIPT=/apps/miniconda3/etc/profile.d/conda.sh
python -c "import ROOT; print(ROOT.gROOT.GetVersion())"
```

Si el módulo ha cambiado, usar la versión que confirme el instructor. El módulo ROOT de Yuca no agrega automáticamente PyROOT al PYTHONPATH.

## Tu espacio personal

Todos los archivos que generes deben quedar en tu cuenta:

```bash
mkdir -p "$HOME/hep-workshop/configs" "$HOME/hep-workshop/logs" \
  "$HOME/hep-workshop/extraction" "$HOME/hep-workshop/results"
python -m pip freeze > "$HOME/hep-workshop/pip-freeze.txt"
```

No instalar paquetes ni modificar los datos compartidos durante el ejercicio. Si el entorno no está disponible o falta una biblioteca, solicitar ayuda antes de continuar.

La cuenta Slurm del ejemplo es `p002`. Si tu proyecto usa otra, reemplazala en los comandos y en la generacion de configuraciones. Continua en [Datos](02_datos.md).

Volver al [programa del curso](../practical-ml-hep/index.md). Después de revisar los datos, continuar con el [análisis y clasificación Higgs](../practical-ml-hep/higgs.md).
