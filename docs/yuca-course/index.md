# Curso reproducible en Yuca

Este curso usa la rama [`opendata_dev`](https://github.com/castaned/ML-integration-CMSSW/tree/opendata_dev) del framework. Es independiente de las instrucciones generales de CERN de este sitio: aqui se trabaja con archivos NanoAOD locales, Conda y Slurm en Yuca.

```text
NanoAOD ROOT (fondo y senal)
  -> procesamiento con filterNanoAOD.py
  -> ROOT procesado -> HDF5
  -> clasificador MLP / autoencoder de anomalias
  -> curvas, metricas y modelos
```

## Ruta del curso

1. [Preparar la cuenta y el entorno](01_entorno.md).
2. [Colocar y revisar NanoAOD](02_datos.md).
3. [Procesar ROOT y convertir a HDF5](03_procesamiento.md).
4. [Entrenar y evaluar el clasificador](04_clasificador.md).
5. [Entrenar un autoencoder con fondo del Modelo Estandar](05_autoencoder.md).
6. [Resolver fallos frecuentes](06_problemas.md).

## Antes de comenzar

Necesitas una cuenta de Yuca, una cuenta/proyecto Slurm autorizado (en el ejemplo, `p002`) y al menos un archivo NanoAOD de fondo y uno de senal. **El curso no redistribuye datos CMS**: el instructor debe indicar el lugar compartido o proporcionar archivos que cada estudiante pueda leer. Hasta que exista esa ruta comun, los comandos usan `$HOME/Open-Data/Data` como ejemplo personal.

Los resultados numericos del ejemplo no son una medicion de fisica. Una puntuacion anomala indica que un evento se parece poco al fondo usado para entrenar; no demuestra nueva fisica. Una busqueda real necesita controles independientes, sistematicas, calibracion y un procedimiento estadistico acordado antes de mirar la senal.

!!! note "Trabajo de cada estudiante"
    Ejecuta el tutorial primero en `opendata_dev`. Para desarrollar cambios, crea despues una rama propia (`git switch -c estudiante-usuario-dev`) y propone una pull request; no hagas push directo a la rama compartida.
