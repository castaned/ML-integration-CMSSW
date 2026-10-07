# 5. Autoencoder para busqueda de anomalias

El autoencoder aprende a reconstruir **solo eventos de fondo del Modelo Estandar** (`Dataset_ID=2`). Un error de reconstruccion grande es una puntuacion de anomalia. Los eventos de senal (`Dataset_ID=1`) se usan unicamente al final para ilustrar una posible respuesta: **nunca entran en el entrenamiento, en la normalizacion ni en la eleccion del umbral**.

El YAML `autoencoder_model_config.yaml` generado por el paso 3 incluye cuatro variables definidas para todos los eventos (`MET_pt`, `nElectron`, `nMuon`, `nLeptons`). Esto evita usar directamente los `-999` de canales inactivos. La normalizacion se aprende solo del subconjunto de fondo de entrenamiento. El fondo se divide en entrenamiento, validacion y prueba con una semilla fija; el umbral es el cuantil 0.99 del error de **validacion de fondo**.

## Prueba y envio

Desde Yuca:

```bash
cd "$HOME/ML-integration-CMSSW/ml_training"
python -m unittest discover -s tests -v
mkdir -p logs
export CONDA_SETUP_SCRIPT=/apps/miniconda3/etc/profile.d/conda.sh
export CONDA_ENV_NAME=ml-open-data
export ML_CONFIG_PATH="$HOME/Open-Data/configs/autoencoder_model_config.yaml"
job=$(sbatch --parsable -A p002 -p cpu -c 6 --mem=16G --time=04:00:00 \
  --job-name=cms_autoencoder --output=logs/job_%j.out --error=logs/job_%j.err \
  --export=ALL --wrap='bash run_training.sh')
echo "Trabajo: $job"
```

Si el directorio de datos compartidos o la cuenta Slurm son diferentes, genera de nuevo los YAML en un espacio personal nuevo o edita **solo** las rutas y la cuenta del YAML personal. No modifiques los HDF5 originales.

## Verificar y estudiar

```bash
sacct -j "$job" --format=JobID,State,ExitCode
grep -E 'Autoencoder training and evaluation completed|\[ERROR\]|Traceback' \
  "logs/job_${job}.out" "logs/job_${job}.err"
python -m json.tool "$HOME/Open-Data/Processed/results_autoencoder/metrics_autoencoder_sm.json"
ls -lh "$HOME/Open-Data/Processed/results_autoencoder"/{best_model_*,loss_*,scores_*,ROC_*,PR_*}
```

El resultado incluye el checkpoint `.pth` con variables, medias, escalas y umbral; un ONNX para reconstruccion; curva de entrenamiento; distribuciones de errores; ROC, precision-recall y un CSV con puntuaciones individuales. La columna `above_threshold` marca candidatos, **no descubrimientos**. La tasa de falsos positivos se estima en fondo de prueba y la eficiencia de ejemplo con senal de prueba.

!!! warning "Limites fisicos"
    Un autoencoder puede reconstruir bien eventos de nueva fisica y marcar como anomalos eventos normales mal modelados. Este ejercicio usa division por eventos, no archivos ni corridas independientes. Para un analisis real hacen falta validacion con otros procesos del Modelo Estandar, incertidumbres sistematicas, control de regiones ciegas, efecto look-elsewhere y revision de la estrategia de seleccion antes de interpretar excesos.

Continua en [Problemas frecuentes](06_problemas.md).
