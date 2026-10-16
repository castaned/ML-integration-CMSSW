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
