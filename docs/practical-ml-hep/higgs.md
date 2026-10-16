# Práctica 1: NanoAOD CMS → análisis → clasificador Higgs

## Muestras de origen

- Señal: [GluGluHToZZTo4L, masa 125 GeV](https://opendata.cern.ch/record/37728), DOI 10.7483/OPENDATA.CMS.4GPD.HQ5T.
- Fondo: [ZZTo4L](https://opendata.cern.ch/record/75589).

Ambas son simulaciones CMS a 13 TeV, UL16 NanoAODv9. No mezclar MiniAOD, variaciones TuneUp/TuneDown ni campañas distintas. El Higgs es parte del SM; en esta clasificación se denomina señal al proceso que queremos separar. A diferencia del autoencoder W′, no es una búsqueda de una partícula nueva.

## Miércoles, primera hora: configurar el sistema y procesar eventos

Comenzar con [Configuración del sistema](../yuca-course/01_entorno.md) (20 minutos) antes de abrir archivos.

### 1. Abrir Events y observar las colecciones (10 min)

Los ROOT originales están en la carpeta compartida del curso. Las rutas se prepararon automáticamente al configurar tu sesión. Ejecutar desde la raíz del repositorio:

```bash
python workshop/student.py inspect
```

Leer la selección común en `configs/selection.yaml`, sin cambiarla. Los archivos Python implementan el análisis y se consultan para entender el procedimiento; no se editan durante este ejercicio.

### 2. Seleccionar y reconstruir (15 min)

La selección educativa exige exactamente cuatro leptones identificados: muones medium con aislamiento relativo ≤0.25 y |η|≤2.4; electrones cutBased≥2 y |η|≤2.5. Todos tienen pT≥5 GeV; ordenados por pT cumplen 20/10/5/5 GeV.

Se forman dos pares de igual sabor y carga opuesta. Z1 es el par cuya masa está más cerca de 91.1876 GeV; Z2 usa los dos leptones restantes. Ventanas comunes para ambos procesos: mZ1=40–120, mZ2=12–120 y m4l=70–180 GeV. **Z2 puede estar fuera de la masa nominal Z: no imponer dos Z on-shell para H125.**

Esta selección omite correcciones, disparadores, identificación avanzada, FSR y estimaciones de fondos reducibles. No es la selección oficial H→ZZ de CMS.

```bash
python workshop/student.py extract
```

Se envía un arreglo de Slurm con **una tarea por archivo NanoAOD**. Un trabajo final espera a que todas las tareas terminen correctamente y reúne sus resultados para generar las gráficas, el HDF5 y el mapa de datasets. En `squeue` el arreglo puede aparecer agrupado como un solo renglón; `squeue -r -u "$USER"` muestra las tareas por separado. Los registros y productos intermedios quedan en tu carpeta personal, junto a la extracción, con sufijo `.parts`. Un archivo sin eventos seleccionados es válido; si falla una tarea, no se genera el conjunto final incompleto.

### 3. Examinar los observables (15 min)

El mismo comando realiza **procesamiento → gráficas → conversión a HDF5**, sin intervención adicional. Produce `observables.pdf/png`, `events.h5`, `cutflow.json`, `provenance.json`, `dataset_map.json` y la copia de configuración. No ejecutar una conversión aparte. El cutflow informa entradas, rechazos por etapa y seleccionados; no es una tabla acumulativa. Verificar cuántos eventos quedan en cada clase. El entrenador exige al menos 20 eventos de cada clase en validación y test; es un mínimo educativo, no garantía de precisión estadística.

El archivo HDF5 contiene una tabla de eventos con doce observables reconstruidos: m4l, mZ1, mZ2, pT4l, pTZ1, pTZ2, suma pT leptónica, los cuatro pT individuales y MET. `Dataset_ID` identifica el proceso de origen según `dataset_map.json`; `EventId` conserva la procedencia. Ninguno entra como variable de entrenamiento. No se usan ramas de verdad de generador como entradas.

**Preguntas:** ¿dónde aparece la masa del Higgs? ¿Por qué necesitamos emparejamiento? ¿Qué ocurre al exigir dos Z cercanos a 91 GeV?

## Identificadores de proceso y clases de la red

El procesamiento utiliza el mismo convenio del framework original: un ID numérico por dataset y un mapa JSON de IDs a nombres. Para este ejemplo, el procesamiento produce automáticamente:

```json
{"1": "Higgs125", "2": "ZZ4L"}
```

Cada evento en HDF5 conserva su `Dataset_ID`. La copia del mapa queda junto a `events.h5` como `dataset_map.json` y también se guarda como metadato del HDF5.

El YAML de entrenamiento define cómo traducir esos IDs a clases de la MLP:

```yaml
data:
  label: Dataset_ID
  num_classes: 2
  class_id_map: {1: 1, 2: 0}
  label_mapping: /ruta/personal/extraction/baseline/dataset_map.json
```

Este bloque es explicativo: las rutas se preparan automáticamente. **No se edita durante las variaciones.** El ID 1 (Higgs125) corresponde a clase 1, señal; el ID 2 (ZZ4L), a clase 0, fondo. Se reutilizan las funciones de etiquetas de `ml_training/utilities/labels.py`. La MLP recibe únicamente los observables, nunca el ID o la clase como entrada.

## Miércoles, segunda hora: entrenar y modificar

### Comparar las variables de entrada

La extracción también genera `input_variables/input_variables.png` y `.pdf`, con las doce variables comparadas entre Higgs125 (señal) y ZZ4L (fondo), además de archivos individuales como `DER_m4l.png` y `PRI_met.png`. Cada proceso se normaliza a área uno y usa los mismos intervalos: se comparan formas, no tasas físicas. Son gráficas descriptivas de todos los eventos seleccionados.

Para una extracción anterior, se pueden regenerar desde el HDF5 sin repetir procesamiento ni entrenamiento. Usar el YAML archivado del entrenamiento y una carpeta de salida nueva:

```bash
python workshop/plot_inputs.py -f "$HOME/hep-workshop/results/higgs_zz_prueba02/config.yaml" --output "$HOME/hep-workshop/results/higgs_zz_prueba02/input_variables"
```

Observar qué variables separan las clases y cuáles tienen formas parecidas. La masa de cuatro leptones permite identificar la resonancia del Higgs cerca de 125 GeV.

### 4. Entrenar la red de referencia (15 min)

La preparación personal ya generó el YAML con las entradas extraídas y las salidas de tu cuenta. No cambiar rutas ni seleccionar otro modelo. Ejecutar:

```bash
python workshop/student.py train --task higgs --role baseline
squeue -u "$USER"
```

El modelo común es una red MLP. El HDF5 es un producto del análisis NanoAOD realizado en el paso anterior, como en la práctica del autoencoder. Entrenamiento/validación/test: 60/20/20 estratificado; escalado ajustado solo con entrenamiento. El programa evalúa validación y guarda curvas y métricas en tu carpeta personal.

### 5. Variar un parámetro del YAML (25 min)

Seguir los [cuatro escenarios por grupo](experiments.md). Abrir con el editor de Open OnDemand el YAML de variación que muestra `student.py files`. Modificar únicamente el campo asignado dentro de `model` y guardar. No modificar Python, Slurm, datos, variables, semilla, etiquetas ni umbral.

```bash
python workshop/student.py train --task higgs --role variation
```

Los valores propuestos están en la guía de grupos. Comparar con la referencia usando validación; la referencia no se modifica. Cada carpeta de resultados conserva su configuración. El programa rechaza cambios ajenos al parámetro asignado y no sobrescribe un entrenamiento anterior.

Una vez cerrada la comparación, congelar el YAML y hacer la evaluación final cuando se indique:

```bash
python workshop/student.py final
```

El programa exige el mismo YAML de variación ya evaluado y guarda el test por separado. No volver a escoger parámetros después de mirar el test.

## Interpretación y entrega

La práctica no aplica pesos de sección eficaz, genWeight, luminosidad ni correcciones: AUC y eficiencia describen la muestra seleccionada, no tasas físicas ni descubrimiento. La separación puede estar dominada por m4l; discutir esta limitación sin cambiar las entradas del ejercicio controlado. Los archivos pequeños sirven para aprender el flujo y no para una medida científica; si quedan pocos eventos, ampliar el conjunto antes de entrenar.

Entregar configuración de selección, cutflow, distribuciones, configuración ML y una comparación con explicación física. El ejercicio ATLAS CSV queda como extensión opcional; sus resultados anteriores no se aplican a este análisis CMS.
