# ATLAS Higgs Challenge: redes profundas en GPU

Esta es la práctica principal del taller. Entrenaremos una red para separar Higgs → ττ de procesos de fondo, con el dataset del [ATLAS Higgs Challenge en CERN Open Data](https://opendata.cern.ch/record/328). Contiene 30 variables físicas ya extraídas; no es NanoAOD. El autoencoder CMS queda como ejemplo exploratorio de un flujo desde NanoAOD y de otra motivación para entrenar redes.

Los datos ya están en `/lustre/cursos/curso07/datos/ATLAS_HiggsChallenge/atlas-higgs-challenge-2014-v2.csv.gz`. No descargarlos ni modificarlos. Las configuraciones y salidas son personales.

## Entorno GPU de Yuca

Yuca utiliza AMD Instinct MI210: se necesita PyTorch con ROCm. El ambiente CPU o una instalación CUDA para NVIDIA no permiten usar estas GPU. Crear una sola vez el ambiente personal:

```bash
source /apps/miniconda3/etc/profile.d/conda.sh
module load rocm/6.4.3
conda create -n ml-hep-gpu python=3.10 pip -y
conda activate ml-hep-gpu
python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/rocm6.4
python -m pip install numpy pandas scikit-learn matplotlib pyyaml h5py
```

Para sesiones posteriores, cargar el módulo y activar `ml-hep-gpu`. El script de entrenamiento también lo hace dentro del trabajo GPU. Esta combinación fue comprobada en Yuca con una operación de matrices sobre MI210; cada cuenta debe poder solicitar los recursos de su proyecto.

## Primer entrenamiento

Desde la raíz de tu repositorio:

```bash
git pull --ff-only origin opendata_dev
mkdir -p "$HOME/hep-workshop/configs" "$HOME/hep-workshop/logs"
cp -n workshop/configs/atlas_higgs_gpu.yaml "$HOME/hep-workshop/configs/atlas_baseline01.yaml"
```

Abrir `hep-workshop/configs/atlas_baseline01.yaml` en el editor de Files de Open OnDemand. Las capas, dropout y parámetros de entrenamiento están en YAML. Para la referencia, conservar los valores de la plantilla:

```yaml
model:
  hidden_dims: [128, 64, 32, 16]
  dropout: 0.1
training:
  device: cuda
  epochs: 20
  batch_size: 4096
  learning_rate: 0.001
  weight_decay: 0.0001
  patience: 6
  weighting: unweighted
  cpu_threads: 4
```

No pegar YAML en la terminal. `cuda` es también el nombre de la interfaz de PyTorch para GPU AMD con ROCm. Los recursos y el ambiente están preparados en el script; no editarlos como parte del experimento.

```bash
sbatch --output="$HOME/hep-workshop/logs/atlas_%j.out" \
  workshop/run_atlas_gpu.slurm "$HOME/hep-workshop/configs/atlas_baseline01.yaml"
squeue -u "$USER"
```

El script solicita proyecto `curso07`, QOS `qoscurso07`, una MI210 y hasta 30 minutos. No acepta una caída silenciosa a CPU si se pidió GPU. La primera ejecución verifica el entrenador completo en tu cuenta; el tiempo real depende del entorno y la cola.

## Qué aprende y cómo evaluamos

Usamos exclusivamente `KaggleSet=t`: 80% para entrenamiento y 20% para validación estratificada, con semilla fija. Los valores ausentes `-999` se reemplazan por medianas de entrenamiento y el escalado se ajusta solo sobre entrenamiento. La pérdida es entropía cruzada binaria sin pesos. Se guarda el mejor modelo según pérdida de validación; la paciencia limita el sobreajuste.

`EventId`, `Label`, `Weight`, `KaggleWeight` y `KaggleSet` nunca entran en la red. Los pesos `KaggleWeight` se usan para evaluar AMS y se reescalan por clase para representar los rendimientos del conjunto `t` completo desde su fracción de validación.

La primera corrida muestra **ROC-AUC sin pesos y AMS interna optimizada en validación**. Esta AMS es exploratoria: se elige el umbral sobre la misma validación. No es una medida independiente ni la puntuación histórica del challenge. Los conjuntos `b` y `v` no se usan para preprocesar, entrenar, elegir modelo o umbral; la evaluación privada se hará en una etapa separada con decisiones congeladas.

## Leer los resultados

```bash
cat "$HOME/hep-workshop/results/atlas_gpu_baseline01/metrics.json"
```

En Files abrir `hep-workshop/results/atlas_gpu_baseline01/training_summary.png`: pérdida de entrenamiento/validación por época, ROC y distribución de puntuaciones. También se guarda PDF, `history.csv`, `validation_scores.csv`, `splits.csv`, `config.yaml`, el preprocesamiento y `best_model.pt`.

Registrar AUC, AMS interna, mejor época, épocas ejecutadas, tiempo y GPU. Para un nuevo experimento, copiar el YAML, variar un solo parámetro y cambiar `output.directory` a una carpeta nueva. Los resultados existentes no se sobrescriben. Una red mayor no garantiza una mejora; conservar iguales los datos, particiones y semillas para comparar.

El ejemplo CMS de [clasificación desde NanoAOD](higgs.md) permanece como material complementario; el [autoencoder](autoencoder.md) ilustra entrenamiento sin etiquetas de señal y error de reconstrucción.

## Experimentos de referencia medidos en Yuca

Estas corridas fueron realizadas con los mismos 200 000 eventos de entrenamiento y 50 000 de validación interna, semilla 16, lote 4096, aprendizaje 0.001 y dropout 0.1. La GPU fue una AMD Instinct MI210; CPU utilizó cuatro hilos. Son observaciones de una corrida por configuración, no promedios ni garantías de tiempo.

| Red | Dispositivo | Épocas | Tiempo medido (s) | AUC validación | AMS interna |
| --- | --- | ---: | ---: | ---: | ---: |
| 128, 64, 32, 16 | CPU | 20 | 39.35 | 0.91048 | 3.5629 |
| 128, 64, 32, 16 | GPU | 20 | 29.95 | 0.90999 | 3.5229 |
| 512, 256, 128, 64 | CPU | 20 | 90.52 | 0.91184 | 3.5380 |
| 512, 256, 128, 64 | GPU | 20 | 30.15 | 0.91112 | 3.4509 |
| 1024, 1024, 512, 512, 256, 128, 64, 32 | GPU | 25 | 39.60 | 0.91140 | 3.5143 |

La aceleración CPU/GPU pasó de 1.31× a 3.00× al ampliar la red de cuatro capas. Más cálculo puede aprovechar mejor la GPU, pero más parámetros no garantizan mejor clasificación: la AUC aumentó ligeramente mientras AMS no mejoró. AUC resume todos los umbrales; AMS usa una selección con pesos físicos.

`fit_seconds` mide el bucle de entrenamiento y la evaluación final del mejor modelo; excluye la espera en cola, lectura inicial y preprocesamiento. No representa el tiempo total desde que se envía el trabajo. Para medir aceleración con más confianza, repetir al menos tres veces y comparar medianas con el mismo número de épocas. Registrar también nodo CPU, hilos, GPU, versión de PyTorch y arquitectura. Para estudiar estabilidad del modelo, variar las semillas de inicialización manteniendo las particiones fijas; el entrenador actual usa una misma semilla para ambas, por lo que cambiarla también cambia la partición y debe indicarse.

### Profundidad y parada temprana

La red de ocho capas se configuró con máximo 200 épocas y `patience: 15`. Su mínimo de pérdida de validación ocurrió en la época 10; se detuvo en la 25 y recuperó el modelo de la época 10. La curva de entrenamiento siguió bajando mientras validación subió: un patrón de sobreajuste.

Para repetir ese ensayo, crear una copia completa del YAML personal y cambiar solo estos campos (sin eliminar los demás):

```yaml
model:
  hidden_dims: [1024, 1024, 512, 512, 256, 128, 64, 32]
  dropout: 0.1
training:
  epochs: 200
  patience: 15
output:
  directory: $HOME/hep-workshop/results/atlas_gpu_deep_earlystop01
```

Guardar como `configs/atlas_gpu_deep_earlystop01.yaml` dentro de tu espacio personal y enviar desde la raíz del repositorio:

```bash
sbatch --time=01:00:00 --output="$HOME/hep-workshop/logs/atlas_deep_%j.out" \
  workshop/run_atlas_gpu.slurm "$HOME/hep-workshop/configs/atlas_gpu_deep_earlystop01.yaml"
```

Si ya existe esa corrida, elegir un nombre nuevo. Un experimento posterior puede cambiar únicamente dropout de 0.1 a 0.3, conservando las capas y la parada temprana, para investigar regularización. No asumir una mejora antes de medirla.

### Registro y conclusiones por equipo

Copiar una fila por entrenamiento en la tabla compartida del curso:

| Grupo/corrida | Capas | Dropout | Aprendizaje | Lote | Dispositivo/hilos | Mejor época | Épocas ejecutadas | Tiempo (s) | AUC | AMS interna | Conclusión |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | | | | |

Compartir el YAML, `metrics.json`, `history.csv` y `training_summary.png`, junto con una conclusión breve: qué cambió, cuánto costó, si mejoró AUC/AMS y qué muestran las pérdidas. Conservar los resultados en carpetas personales distintas; compartir solo las entregas solicitadas. No afirmar mejoras significativas por diferencias pequeñas de una única corrida.

## Benchmarks publicados del Higgs Challenge

La referencia histórica usa **AMS en el conjunto privado del challenge**, no AUC. La [publicación del challenge, tabla 2](https://proceedings.mlr.press/v42/cowa14.pdf), informa:

| Método | AMS privada histórica |
| --- | ---: |
| TMVA de referencia | 3.19956 |
| MultiBoost de referencia | 3.40488 |
| Solución ganadora, conjunto de redes profundas | 3.80581 |

Usar aproximadamente **3.40** como referencia de partida histórica y **3.81** como referencia ganadora. El ganador combinaba modelos; no era simplemente una red individual más grande. Estos valores contextualizan el ejercicio, pero nuestra AMS interna de aproximadamente 3.45–3.56 no permite afirmar que superamos MultiBoost ni que estamos cerca del ganador: cambia el conjunto de evaluación y el umbral se optimizó sobre la propia validación.

Para una comparación numérica externa, congelar arquitectura, modelo, preprocesamiento y regla de selección antes de evaluar `KaggleSet=v`. Reproducir la definición oficial de AMS, su regularización y los pesos `KaggleWeight` de esa partición, sin reutilizar el reescalado de validación `t`. Documentar también si se entrena con una fracción de `t` o con todo `t`, y cualquier diferencia respecto al protocolo histórico. Nunca buscar el mejor umbral mirando las etiquetas privadas. El entrenador inicial todavía no realiza esta evaluación privada: hasta añadir esa etapa, reportar los números históricos y las métricas internas en tablas separadas.
