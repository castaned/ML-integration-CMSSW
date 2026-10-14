# Preparación del instructor

El taller ocupa **miércoles 3 horas y jueves 1 hora**. Preparar datos y entorno antes de clase; no pedir a cada alumno descargas ROOT ni crear el conjunto CMS durante la sesión.

## Datos ATLAS: descargar una vez

En tu copia `opendata_dev`, ejecutar en una sesión autorizada para transferencia:

```bash
python workshop/download_higgs.py \
  --output "$HOME/Open-Data/Workshop/atlas-higgs-challenge-2014-v2.csv.gz"
```

Fuente: [CERN Open Data 328](https://opendata.cern.ch/record/328), DOI `10.7483/OPENDATA.ATLAS.ZBP2.M5T8`. Archivo comprimido 65 630 848 bytes; Adler32 `e4717bbe`, verificado contra el registro. CSV completo: 818 238 eventos. El programa verifica tamaño y checksum, registra procedencia y evita sobrescribir archivos. Una descarga incompleta conserva `.part`; comprobar la causa antes de reintentar con una ruta nueva.

La práctica usa una selección de 50 000 eventos para reducir el tiempo. Es el dataset del Higgs ML Challenge, no NanoAOD CMS. Son etiquetas binarias; no se identifican por separado los fondos del archivo.

## Datos CMS: reutilizar los HDF5 validados

Punto de partida del instructor en Yuca:

```bash
python scripts/check_dyjets_ht_pilot.py \
  -f "$HOME/Open-Data/autoencoder_dyjets_ht_10features_config.yaml"
```

Las rutas conocidas del piloto están bajo `/lustre/home/acastaneda/Open-Data/Processed/`: DYJets en `h5_dyjets_ht/DYJets` y WZ/ZZ en `h5_sm_cocktail/`. La ruta W′ debe tomarse de la configuración verificada, no inferirse del nombre de una carpeta.

Preparar una copia llamada `autoencoder_reference.yaml` con todas las entradas **absolutas**, con las mismas características/etiquetas y una salida que los alumnos reemplazarán. Si se mueven/copían archivos, conservar nombres y contenidos y repetir el preflight. Confirmar lectura con una cuenta de alumno. Solicitar al soporte una ubicación compartida autorizada; no abrir permisos de todo el HOME ni compartir credenciales. Anunciar ruta CSV, ruta YAML, cuenta Slurm y entorno conda.

## Entorno y recursos

Usar un entorno probado con Python ≥3.10. Dependencias Higgs en `workshop/requirements.txt`; CMS necesita además PyTorch, h5py, onnx y las dependencias ya utilizadas por `ml_training`. No reemplazar PyTorch del entorno funcional de Yuca. Añadir dependencias faltantes en una copia personal o un entorno del curso con apoyo local.

```bash
source /apps/miniconda3/etc/profile.d/conda.sh
conda activate ml-open-data
python -c "import pandas, sklearn, yaml, torch, h5py, onnx; print('OK')"
```

El ejecutor acepta `WORKSHOP_CONDA_ENV` y `CONDA_SETUP_SCRIPT`. Cuenta Slurm se pasa con `sbatch --account=...`; no imponer la cuenta del instructor a todos los participantes. Reserva inicial: 2 CPU, 6 GB, 30 minutos; hacer un ensayo con la cola real y ajustar si hace falta. No prometer GPU ni ejecución instantánea.

## Ensayo completo previo

1. Descargar y verificar el CSV.
2. Probar regresión logística, boosted y MLP con 50 000 eventos y guardar tiempos/avisos.
3. Probar el YAML CMS con una cuenta de alumno, ejecutar preflight y entrenar una referencia completa.
4. Comprobar que los PDFs/PNGs abren desde Open OnDemand y que cada equipo tiene directorio personal.
5. Preparar resultados de respaldo si la cola no permite completar un entrenamiento durante la hora. Identificarlos como resultados del instructor.

Los tiempos medidos en una laptop no validan los tiempos de Yuca. Los resultados históricos del póster tampoco son métricas garantizadas del taller.

## Dinámica en cuatro horas

Equipos de dos participantes. Asignar una variación diferente a cada equipo; comparar al cierre. Proporcionar configuraciones de referencia y revisar sus copias antes de enviar trabajos. El miércoles congelar el clasificador antes de test; el jueves declarar explícitamente el carácter exploratorio de la referencia W′.

## Criterios de evaluación

| Criterio | Evidencia |
| --- | --- |
| Procedencia física | Distingue simulación ATLAS/CMS y señal/fondo |
| Reproducibilidad | Configuraciones, semilla y carpetas propias |
| Comparación justa | Una modificación y particiones constantes |
| Interpretación | AUC/eficiencia/aceptación con definición y pesos |
| Limitaciones | No confunde separación ML con descubrimiento |

El acceso a Yuca y los datos de los estudiantes se preparan localmente: la documentación publicada no implica que estas acciones ya se hayan ejecutado en el clúster.
