# Practical Machine Learning in HEP

Dos jornadas: miércoles de tres horas y jueves de una hora en el clúster Yuca: **clasificación de Higgs con ATLAS Open Data** y **detección de anomalías con CMS Open Data**. Cada equipo modifica un modelo, registra sus resultados y justifica una decisión física.

Este taller complementa el [curso Yuca de Open Data](../yuca-course/index.md). Aquí empezamos con datos preparados; el curso anterior explica la selección NanoAOD y conversión ROOT a HDF5.

## Programa: miércoles y jueves

| Jornada | Distribución del tiempo | Producto del alumno |
| --- | --- | --- |
| Miércoles, hora 1 | 10 min física/datos; 10 min entorno; 25 min clasificador; 15 min interpretación | ROC de validación y referencia |
| Miércoles, hora 2 | 10 min repaso; 30 min una mejora; 10 min test final; 10 min discusión | Comparación y evaluación final Higgs |
| Miércoles, hora 3 | 10 min anomalías; 10 min datos CMS; 25 min entrenamiento; 15 min diagnóstico | Referencia de autoencoder |
| Jueves, hora 1 | 10 min repaso; 25 min una variación; 15 min comparación; 10 min presentación | Tabla y conclusiones de cada equipo |

Las colas pueden afectar los tiempos: el instructor debe probar las asignaciones antes del taller y conservar resultados de referencia. No se garantiza un tiempo de entrenamiento universal. Cada equipo realiza una mejora; los ejercicios restantes son extensiones.

## Dos preguntas físicas

1. **Supervisado:** ¿podemos distinguir Higgs → ττ de eventos que producen una firma parecida? Usamos simulación oficial ATLAS, con etiquetas de señal/fondo del [registro CERN Open Data 328](https://opendata.cern.ch/record/328). El fondo mezcla Z→ττ, pares de top y W. Este archivo etiqueta señal/fondo, no el proceso individual: no permite una clasificación multiclase de esos fondos.
2. **No supervisado:** ¿qué eventos se reconstruyen mal después de aprender una referencia del sector electrodébil del SM? Usamos DYJets HT 70–100, WZ y ZZ de CMS; W′→WZ→3ℓν de 1 TeV es una referencia de evaluación.

Son **simulaciones abiertas**, no etiquetas de procesos medidas en colisiones reales. No combinamos eventos ATLAS y CMS en un mismo entrenamiento.

## Antes de empezar

El instructor comunica cuenta Slurm, entorno conda y dos rutas compartidas: CSV de ATLAS y YAML de referencia CMS con rutas absolutas. Los alumnos leen esos datos y escriben únicamente en su propio HOME.

Desde una terminal de Yuca:

```bash
source /apps/miniconda3/etc/profile.d/conda.sh
conda activate ml-open-data
git clone --branch opendata_dev https://github.com/castaned/ML-integration-CMSSW.git "$HOME/ML-integration-CMSSW"
cd "$HOME/ML-integration-CMSSW"
mkdir -p "$HOME/hep-workshop/configs" "$HOME/hep-workshop/logs"
python -c "import pandas, sklearn, yaml, torch, h5py, onnx; print('Entorno listo')"
```

Si ya tienes el repositorio: entrar en él, comprobar `git branch --show-current` y ejecutar `git pull --ff-only origin opendata_dev`. No clonar encima de una carpeta existente. Si falta una dependencia, avisar al instructor; no modificar un entorno compartido durante la clase. Estos ejercicios preparados no requieren ROOT.

## Ruta de aprendizaje

- [Preparación del instructor](instructor.md)
- [Miércoles, horas 1 y 2: Higgs frente a fondo](higgs.md)
- [Miércoles, hora 3, y jueves: autoencoder CMS](autoencoder.md)
- [Bitácora de experimentos](experiments.md)

Código en [`workshop/`, rama opendata_dev](https://github.com/castaned/ML-integration-CMSSW/tree/opendata_dev/workshop). Uso de cómputo de alto rendimiento: clúster ACARUS de la Universidad de Sonora.
