# Datos compartidos: entender NanoAOD

**No debes descargar los datasets.** Los archivos originales del curso estarán disponibles en una carpeta compartida de Yuca. Esa carpeta se utiliza para lectura; las selecciones, tablas y modelos se guardan en tu cuenta.

## 1. Identificar la ruta del curso

Sustituir `/RUTA/COMPARTIDA/NanoAOD` por la ruta anunciada durante el curso. Es un marcador, no una ruta que ya hayamos verificado:

```bash
export COURSE_DATA=/RUTA/COMPARTIDA/NanoAOD
ls "$COURSE_DATA/Higgs125"
ls "$COURSE_DATA/ZZ4L"
```

Se esperan archivos `.root` de Higgs125→ZZ→4L y ZZ→4L. Los registros CERN Open Data permiten conocer su procedencia; no son instrucciones para descargarlos durante la clase.

## 2. Comprobar lectura y entender Events

Desde una terminal de tu propia cuenta:

```bash
python - <<'PY'
import os
from pathlib import Path
import uproot
base = Path(os.environ['COURSE_DATA'])
for sample in ('Higgs125', 'ZZ4L'):
    files = sorted((base / sample).glob('*.root'))
    if not files:
        raise RuntimeError(f'No hay ROOT visibles en {base / sample}')
    with uproot.open(files[0]) as source:
        tree = source['Events']
        print(sample, 'archivo:', files[0].name, 'eventos:', tree.num_entries)
        print(tree.arrays(['nMuon', 'nElectron', 'MET_pt'], entry_stop=3))
PY
```

Cada entrada de Events corresponde a un evento; las colecciones Electron y Muon contienen cantidades variables de partículas. Las masas de candidatos no se toman como etiquetas: se construirán a partir de los leptones seleccionados.

Si no aparecen archivos o no puedes abrirlos, detener el procesamiento y solicitar ayuda con la ruta o los permisos. No copiar los datasets a tu HOME para intentar resolver un fallo de acceso.

## 3. Separar entradas compartidas de salidas personales

```text
Carpeta compartida del curso (lectura)
  Higgs125/*.root
  ZZ4L/*.root

Tu cuenta: $HOME/hep-workshop/ (escritura)
  configs/       YAML personales
  extraction/    observables y conteos de selección
  logs/          registros de trabajos
  results/       modelos, métricas y gráficas
```

No subir los ROOT al repositorio ni modificar archivos compartidos. Cada experimento debe tener una carpeta de salida nueva para conservar la referencia.

Continuar con [Análisis de NanoAOD y clasificación Higgs](../practical-ml-hep/higgs.md): seleccionar leptones → reconstruir candidatos → extraer observables → entrenar y evaluar.
