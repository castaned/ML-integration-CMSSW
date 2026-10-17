# CERN Open Data: uso del framework

Esta sección documenta el modo `open_data` de **ML-integration-CMSSW** para trabajar con archivos NanoAOD públicos de CMS en un clúster local o institucional. Los procesos se configuran mediante YAML.

**NanoAOD (ROOT) → selección de eventos → ROOT procesado → HDF5 → entrenamiento y evaluación.**

## Procedimiento

1. [Preparar el entorno y el repositorio](01_entorno.md).
2. [Localizar y comprobar los archivos NanoAOD](02_datos.md).
3. [Ejecutar el procesamiento y la conversión a HDF5](03_procesamiento.md).
4. Entrenar un [clasificador MLP](04_clasificador.md) o un [autoencoder](05_autoencoder.md).
5. [Consultar registros y resolver problemas](06_problemas.md).

El modo `open_data` lee archivos accesibles desde los nodos del clúster. No requiere consultar DAS ni generar un proxy GRID para procesar archivos locales. Las instrucciones de LXPLUS, CMSSW y autenticación GRID de las otras secciones corresponden al flujo de infraestructura CERN.

Las rutas, la cuenta Slurm y los recursos se ajustan a la instalación utilizada. Los nombres `fondo` y `senal` identifican las dos muestras del ejemplo general; el procesamiento conserva sus identificadores en `Dataset_ID` y en el mapa de datasets.

La documentación docente y los benchmarks del taller se mantienen en [Practical Machine Learning for HEP Data Analysis](https://castaned.github.io/practical-ml-hep/).
