# Práctica 1: NanoAOD CMS → análisis → clasificador Higgs

## Muestras de origen

- Señal: [GluGluHToZZTo4L, masa 125 GeV](https://opendata.cern.ch/record/37728), DOI 10.7483/OPENDATA.CMS.4GPD.HQ5T.
- Fondo: [ZZTo4L](https://opendata.cern.ch/record/75589).

Ambas son simulaciones CMS a 13 TeV, UL16 NanoAODv9. No mezclar MiniAOD, variaciones TuneUp/TuneDown ni campañas distintas. El Higgs es parte del SM; en esta clasificación se denomina señal al proceso que queremos separar. A diferencia del autoencoder W′, no es una búsqueda de una partícula nueva.

## Miércoles, primera hora: procesar eventos

### 1. Abrir Events y observar las colecciones (10 min)

El instructor proporciona los ROOT originales en una carpeta compartida. Desde la raíz del repositorio:

```bash
export NANO_FILE=/RUTA/COMPARTIDA/Higgs125/ARCHIVO.root
python - <<'PY'
import os, uproot
with uproot.open(os.environ['NANO_FILE']) as f:
    t=f['Events']
    print('Eventos:',t.num_entries)
    print(t.keys(filter_name='Muon_*')[:20])
    print(t.arrays(['nMuon','nElectron','MET_pt'],entry_stop=5))
PY
cp workshop/configs/cms_fourleptons.yaml "$HOME/hep-workshop/configs/selection.yaml"
```

Editar `samples[].files`: poner las rutas absolutas a los ROOT de cada proceso. No escribir allí el archivo ya seleccionado. Se leen solo las ramas necesarias; la extracción usa bloques de 2000 eventos.

### 2. Seleccionar y reconstruir (20 min)

La selección educativa exige exactamente cuatro leptones identificados: muones medium con aislamiento relativo ≤0.25 y |η|≤2.4; electrones cutBased≥2 y |η|≤2.5. Todos tienen pT≥5 GeV; ordenados por pT cumplen 20/10/5/5 GeV.

Se forman dos pares de igual sabor y carga opuesta. Z1 es el par cuya masa está más cerca de 91.1876 GeV; Z2 usa los dos leptones restantes. Ventanas comunes para ambos procesos: mZ1=40–120, mZ2=12–120 y m4l=70–180 GeV. **Z2 puede estar fuera de la masa nominal Z: no imponer dos Z on-shell para H125.**

Esta selección omite correcciones, disparadores, identificación avanzada, FSR y estimaciones de fondos reducibles. No es la selección oficial H→ZZ de CMS.

```bash
sbatch --account=CUENTA_DEL_CURSO --output="$HOME/hep-workshop/logs/%j.out"   workshop/run_cpu.slurm extract "$HOME/hep-workshop/configs/selection.yaml"   "$HOME/hep-workshop/extraction/baseline"
```

### 3. Examinar los observables (15 min)

La extracción crea `events.csv`, `cutflow.json`, `provenance.json`, la copia de configuración y `observables.pdf/png`. El cutflow informa entradas, rechazos por etapa y seleccionados; no es una tabla acumulativa. Verificar cuántos eventos quedan en cada clase. El entrenador exige al menos 20 eventos de cada clase en validación y test; es un mínimo educativo, no garantía de precisión estadística.

La tabla contiene doce observables reconstruidos: m4l, mZ1, mZ2, pT4l, pTZ1, pTZ2, suma pT leptónica, los cuatro pT individuales y MET. `Label` viene del proceso simulado de origen; `EventId` conserva la procedencia y nunca es una variable de entrenamiento. No se usan ramas de verdad de generador como entradas.

**Preguntas:** ¿dónde aparece la masa del Higgs? ¿Por qué necesitamos emparejamiento? ¿Qué ocurre al exigir dos Z cercanos a 91 GeV?

### 4. Entrenar con NUESTRA extracción (15 min)

```bash
cp workshop/configs/cms_higgs_classifier.yaml "$HOME/hep-workshop/configs/classifier.yaml"
```

Editar `data.input` con la ruta de `extraction/baseline/events.csv`.

```bash
sbatch --account=CUENTA_DEL_CURSO --output="$HOME/hep-workshop/logs/%j.out"   workshop/run_cpu.slurm higgs "$HOME/hep-workshop/configs/classifier.yaml"   "$HOME/hep-workshop/results/classifier_baseline"
```

El CSV es **un producto del análisis del alumno**, no el dato de origen. Sirve de interfaz entre reconstrucción y ML; puede sustituirse por HDF5 en una extensión. Entrenamiento/validación/test: 60/20/20 estratificado, semilla 16; escalado ajustado solo con entrenamiento. Por defecto se evalúa únicamente validación. Abrir `classification.pdf` y `metrics.json`.

## Miércoles, segunda hora: cambiar una decisión

Elegir una variación por equipo, con configuración y carpeta nuevas:

| Cambio | Acción | Qué discutir |
| --- | --- | --- |
| Identificación/aislamiento | Cambiar `muon_iso_max` o pT en selection.yaml y repetir extracción | Cutflow, representatividad y estadística |
| Variables | Retirar DER_m4l del clasificador | Dependencia de la separación respecto a la masa |
| Modelo | `model.type: boosted` o `mlp` | Relaciones no lineales y sobreajuste |
| Umbral | `background_acceptance: 0.05` | Eficiencia Higgs frente a rechazo del fondo |

Comparaciones de modelos/variables: mantener eventos y semilla. Comparaciones de selección: cambian los eventos, por tanto no atribuir la mejora únicamente al modelo. Las métricas por sí solas no reflejan la pérdida de rendimiento por rechazar eventos antes de entrenar.

Congelar una configuración después de comparar validación; luego una sola evaluación final:

```bash
sbatch --account=CUENTA_DEL_CURSO --output="$HOME/hep-workshop/logs/%j.out"   workshop/run_cpu.slurm higgs-final "$HOME/hep-workshop/configs/classifier.yaml"   "$HOME/hep-workshop/results/classifier_final"
```

El ejecutor reentrena con la misma partición/semilla y mantiene el umbral de validación. No volver a escoger parámetros después de ver test.

## Interpretación y entrega

La práctica no aplica pesos de sección eficaz, genWeight, luminosidad ni correcciones: AUC y eficiencia describen la muestra seleccionada, no tasas físicas ni descubrimiento. La separación puede estar dominada por m4l; la ablación permite discutirlo. Los archivos pequeños sirven para aprender el flujo y no para una medida científica; si quedan pocos eventos, ampliar el conjunto antes de entrenar.

Entregar configuración de selección, cutflow, distribuciones, configuración ML y una comparación con explicación física. El ejercicio ATLAS CSV queda como extensión opcional; sus resultados anteriores no se aplican a este análisis CMS.
