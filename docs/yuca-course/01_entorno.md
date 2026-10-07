# 1. Cuenta, repositorio y entorno

Inicia sesion en Yuca y clona la rama del curso:

```bash
cd "$HOME"
git clone --branch opendata_dev https://github.com/castaned/ML-integration-CMSSW.git
cd ML-integration-CMSSW
git branch --show-current
git status -sb
```

La rama debe ser `opendata_dev`. Si el repositorio ya existe, usa `git pull --ff-only origin opendata_dev` desde esa rama. Si `git status -sb` muestra cambios locales, revisalos antes de actualizar.

## Conda y ROOT

```bash
module load root/6.24.08
source /apps/miniconda3/etc/profile.d/conda.sh
conda create -n ml-open-data python=3.10 -y
conda activate ml-open-data
export PYTHONPATH="$(root-config --libdir):${PYTHONPATH:-}"
```

La creacion del entorno se hace **una sola vez**. En sesiones posteriores repite `module load`, `source`, `conda activate` y `export PYTHONPATH`. El modulo ROOT de Yuca no agrega automaticamente PyROOT al `PYTHONPATH`.

Instala las bibliotecas necesarias en el entorno activo:

```bash
python -m pip install pyyaml uproot awkward tables h5py numpy \
  'torch>=2.5,<3' 'scikit-learn>=1.6,<2' 'ray[tune]==2.42.1' \
  matplotlib onnx onnxscript onnxruntime 'mlflow==2.20.2'
python -m pip check
python -c 'import ROOT, uproot, tables, torch, ray, onnxscript; print("Entorno listo:", ROOT.gROOT.GetVersion())'
```

Si `conda activate` indica `Run conda init`, vuelve a ejecutar `source /apps/miniconda3/etc/profile.d/conda.sh`. Evita `pip install --user`: los paquetes deben quedar en `ml-open-data`. Para un registro exacto de versiones despues de instalar, ejecuta `python -m pip freeze > "$HOME/Open-Data/pip-freeze.txt"`.

La cuenta Slurm del ejemplo es `p002`. Si tu proyecto usa otra, reemplazala en los comandos y en la generacion de configuraciones. Continua en [Datos](02_datos.md).
