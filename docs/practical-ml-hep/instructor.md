# Preparación del instructor

El taller ocupa **miércoles 3 horas y jueves 1 hora**. Preparar datos y entorno antes de clase; no pedir a cada alumno descargas ROOT ni crear el conjunto CMS durante la sesión.

## NanoAOD Higgs/ZZ: descargar originales una vez

```bash
python workshop/download_cms.py --output "$HOME/Open-Data/Workshop/NanoAOD"
```

Los archivos más pequeños de ZZ dieron solo 20 eventos seleccionados en la primera prueba; el piloto usa dos archivos de fondo mayores. Revisar la estadística después de los cortes es parte de la preparación.

El manifiesto `workshop/configs/cms_nanoaod_sources.json` contiene dos ROOT originales pequeños por proceso, URLs del portal, tamaño y Adler32. La descarga verifica ambos y conserva la procedencia. Total aproximado: 247 MB. Es un piloto educativo; inspeccionar el número seleccionado y ampliar archivos del mismo registro si hace falta.

Registros: [Higgs125→ZZ→4L](https://opendata.cern.ch/record/37728) y [ZZ→4L](https://opendata.cern.ch/record/75589), CMS UL16 NanoAODv9. Comunicar rutas absolutas y permisos de lectura a los alumnos. Ellos ejecutan selección y extracción en carpetas propias; no proporcionar solo la tabla final. Guardar una extracción de respaldo identificada como referencia del instructor si la cola falla.

## Datos CMS: reutilizar los HDF5 validados

Punto de partida del instructor en Yuca:

```bash
python scripts/check_dyjets_ht_pilot.py \
  -f "$HOME/Open-Data/autoencoder_dyjets_ht_10features_config.yaml"
```

Las rutas conocidas del piloto están bajo `/lustre/home/acastaneda/Open-Data/Processed/`: DYJets en `h5_dyjets_ht/DYJets` y WZ/ZZ en `h5_sm_cocktail/`. La ruta W′ debe tomarse de la configuración verificada, no inferirse del nombre de una carpeta.

Preparar una copia llamada `autoencoder_reference.yaml` con todas las entradas **absolutas**, con las mismas características/etiquetas y una salida que los alumnos reemplazarán. Si se mueven/copían archivos, conservar nombres y contenidos y repetir el preflight. Confirmar lectura con una cuenta de alumno. Solicitar al soporte una ubicación compartida autorizada; no abrir permisos de todo el HOME ni compartir credenciales. Anunciar ruta NanoAOD, ruta YAML, cuenta Slurm y entorno conda.

## Entorno y recursos

Usar un entorno probado con Python ≥3.10. Dependencias Higgs en `workshop/requirements.txt`; CMS necesita además PyTorch, h5py, onnx y las dependencias ya utilizadas por `ml_training`. No reemplazar PyTorch del entorno funcional de Yuca. Añadir dependencias faltantes en una copia personal o un entorno del curso con apoyo local.

```bash
source /apps/miniconda3/etc/profile.d/conda.sh
conda activate ml-open-data
python -c "import pandas, sklearn, yaml, uproot, awkward, torch, h5py, onnx; print('OK')"
```

El ejecutor acepta `WORKSHOP_CONDA_ENV` y `CONDA_SETUP_SCRIPT`. Cuenta Slurm se pasa con `sbatch --account=...`; no imponer la cuenta del instructor a todos los participantes. Reserva inicial: 2 CPU, 6 GB, 30 minutos; hacer un ensayo con la cola real y ajustar si hace falta. No prometer GPU ni ejecución instantánea.

## Ensayo completo previo

1. Descargar/verificar NanoAOD y probar lectura de Events.
2. Procesar cuatro leptones, revisar cutflow y probar el clasificador con la tabla extraída; guardar tiempos/avisos.
3. Probar el YAML CMS con una cuenta de alumno, ejecutar preflight y entrenar una referencia completa.
4. Comprobar que los PDFs/PNGs abren desde Open OnDemand y que cada equipo tiene directorio personal.
5. Preparar resultados de respaldo si la cola no permite completar un entrenamiento durante la hora. Identificarlos como resultados del instructor.

Los tiempos medidos en una laptop no validan los tiempos de Yuca. Los resultados históricos del póster tampoco son métricas garantizadas del taller.

## Dinámica en cuatro horas

Equipos de dos participantes. Asignar una variación diferente a cada equipo; comparar al cierre. Proporcionar configuraciones de referencia y revisar sus copias antes de enviar trabajos. El miércoles congelar el clasificador antes de test; el jueves declarar explícitamente el carácter exploratorio de la referencia W′.

## Criterios de evaluación

| Criterio | Evidencia |
| --- | --- |
| Procedencia física | Identifica procedencia CMS y señal/fondo |
| Reproducibilidad | Configuraciones, semilla y carpetas propias |
| Comparación justa | Una modificación y particiones constantes |
| Interpretación | AUC/eficiencia/aceptación con definición y pesos |
| Limitaciones | No confunde separación ML con descubrimiento |

El acceso a Yuca y los datos de los estudiantes se preparan localmente: la documentación publicada no implica que estas acciones ya se hayan ejecutado en el clúster.
