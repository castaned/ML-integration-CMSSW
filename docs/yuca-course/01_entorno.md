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

## Crear tu entorno personal por primera vez

Cada participante recibe una cuenta de Yuca y **crea su propio entorno conda**. La cuenta nueva no incluye el entorno del curso ya instalado. Ejecutar estos pasos una sola vez, desde la carpeta del repositorio:

```bash
source /apps/miniconda3/etc/profile.d/conda.sh
conda create -n ml-open-data python=3.10 -y
conda activate ml-open-data
```

Si ya completaste esta creación en tu cuenta, activar el entorno existente en lugar de crearlo otra vez. No usar el entorno personal de otro participante.

## Instalar las dependencias del curso

Con `ml-open-data` activo y dentro de `ML-integration-CMSSW`:

```bash
python -m pip install -r workshop/requirements-yuca.txt
python -m pip install 'torch>=2.5,<3' --index-url https://download.pytorch.org/whl/cpu
python -m pip check
```

Las prácticas se envían a nodos CPU. Se utiliza la distribución CPU de PyTorch del [índice oficial](https://pytorch.org/get-started/locally/). La instalación de bibliotecas se hace en tu entorno personal, no en una carpeta compartida. No utilizar `sudo` ni `pip install --user`.

Este paso descarga bibliotecas de software; **los datasets del curso no se descargan**, se leen desde la carpeta compartida.

## Verificar antes de continuar

```bash
python - <<'PY'
import sys
import pandas, sklearn, yaml, uproot, awkward
import torch, h5py, onnx
print('Python:', sys.version.split()[0])
print('PyTorch:', torch.__version__)
print('Entorno del curso listo')
PY
```

Continuar solo si termina sin errores. Si no se encuentra conda, falla una instalación o falta una biblioteca, solicitar ayuda antes de procesar datos. No es necesario cargar ROOT/PyROOT para las prácticas principales: el ejemplo Higgs lee NanoAOD con uproot.

## Tu espacio personal

Todos los archivos que generes deben quedar en tu cuenta:

```bash
mkdir -p "$HOME/hep-workshop/configs" "$HOME/hep-workshop/logs" \
  "$HOME/hep-workshop/extraction" "$HOME/hep-workshop/results"
python -m pip freeze > "$HOME/hep-workshop/pip-freeze.txt"
```

Después de completar la instalación y la verificación, mantener el entorno para las prácticas y no modificar los datos compartidos.

## Al volver a iniciar sesión

En sesiones posteriores no repetir la creación del entorno ni la instalación de paquetes. Ejecutar únicamente:

```bash
source /apps/miniconda3/etc/profile.d/conda.sh
conda activate ml-open-data
cd "$HOME/ML-integration-CMSSW"
```

## Preparar tus configuraciones personales

Con la sesión y el entorno activos, ejecutar el comando de preparación comunicado para tu grupo. La configuración institucional contiene las rutas compartidas y la cuenta de cómputo; **no debes editarla**. Ejemplo de forma del comando (la ruta real se anunciará en el curso):

```bash
python workshop/student.py prepare --settings /RUTA/COMPARTIDA/course_settings.yaml --group 1
```

Esta preparación se realiza una sola vez. Genera automáticamente la selección común, los YAML de referencia y variación del grupo, las rutas de entrada y las salidas en tu cuenta. No completar manualmente nombres de ROOT, cuentas Slurm ni carpetas de resultados.

Para ver cuáles son tus YAML:

```bash
python workshop/student.py files
```

**Solo se modifica el parámetro asignado dentro de `model` en el YAML de variación.** La referencia y las demás secciones permanecen fijas. Los comandos siguientes son iguales para todos los grupos.

Continuar con [Entender los datos compartidos](02_datos.md).
