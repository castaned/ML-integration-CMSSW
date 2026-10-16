# Practical Machine Learning in HEP

Dos jornadas: miércoles de tres horas y jueves de una hora en el clúster Yuca: **ATLAS Higgs Challenge con redes profundas en GPU como práctica principal** y **autoencoder CMS desde NanoAOD como exploración complementaria**. Cada equipo modifica un modelo, registra sus resultados y justifica una decisión física.

**Este es el curso Yuca Open Data, con el nombre Practical Machine Learning in HEP.** Es una única ruta de aprendizaje: configuración del sistema → datos abiertos → entrenamiento en GPU mediante YAML → evaluación y comparación. El ejemplo complementario CMS muestra el procesamiento desde NanoAOD.

## Flujo del análisis en Yuca

![Flujo del análisis: datos compartidos, selección, observables, entrenamiento, evaluación y comparación](../assets/workshop/flujo_analisis_yuca.svg)

Los archivos de entrada se leen desde la carpeta compartida. Cada participante guarda el procesamiento y los resultados en su cuenta personal, y después comparte las figuras y métricas de su grupo.

[Descargar PNG](../assets/workshop/flujo_analisis_yuca.png) · [Descargar SVG vectorial](../assets/workshop/flujo_analisis_yuca.svg)

## Empezar aquí

1. [Primer acceso SSH y activación de la cuenta con 2FA](../yuca-course/00_acceso.md), una sola vez y preferentemente antes del taller.
2. [Clonar el repositorio, crear tu entorno conda e instalar dependencias](../yuca-course/01_entorno.md), con la cuenta ya activada.
3. [Datos abiertos, formato NanoAOD y revisión de archivos](../yuca-course/02_datos.md).
4. [Práctica principal: ATLAS Higgs Challenge en GPU, controlado por YAML](atlas-gpu.md).
   Material complementario: [procesamiento CMS Higgs/ZZ desde NanoAOD](higgs.md).
5. [Ejemplo 2: autoencoder CMS multileptónico](autoencoder.md).
6. [Tablas y preguntas para tus experimentos ATLAS](atlas-experiments.md).
7. [Entrega en carpeta compartida y comparación colectiva](delivery.md).

Antes de entrenar, comprobar el entorno, las rutas compartidas y el acceso a GPU. Los datos del curso ya estarán disponibles en una carpeta compartida: no es necesario descargarlos. Cada participante crea su entorno conda, instala las bibliotecas, verifica la instalación y prepara su espacio personal antes de las prácticas.

## Programa: miércoles y jueves

| Jornada | Distribución del tiempo | Producto del alumno |
| --- | --- | --- |
| Miércoles, hora 1 | Entorno GPU, datos ATLAS, variables y primer entrenamiento | Referencia reproducible |
| Miércoles, hora 2 | Curvas de aprendizaje, ROC, AMS y variaciones YAML | Comparación de entrenamientos |
| Miércoles, hora 3 | Experimentos de arquitectura, aprendizaje y regularización | Tabla y discusión por equipos |
| Jueves, hora 1 | Conclusiones del challenge e introducción exploratoria al autoencoder CMS | Comparación de motivaciones y redes |

Las colas pueden afectar los tiempos: consultar el estado de los trabajos y sus registros. La instalación inicial depende de las descargas y puede ocupar más tiempo que el previsto; completar el capítulo de configuración antes de entrar a los ejemplos. No se garantiza un tiempo de entrenamiento universal. Cada equipo realiza una mejora; los ejercicios restantes son extensiones.

## Dos preguntas físicas

1. **Supervisado (principal):** Higgs→ττ frente a fondos del ATLAS Higgs Challenge. Las 30 variables ya están extraídas; el alumno configura redes profundas con YAML y entrena en GPU.
2. **No supervisado:** DYJets HT 70–100, WZ y ZZ de CMS como referencia electrodébil multileptónica; W′→WZ→3ℓν como referencia de evaluación.

Son simulaciones abiertas. El análisis CMS desde NanoAOD queda como material complementario. La AMS interna de validación no equivale a la puntuación privada histórica del challenge.

## Antes de empezar

Utilizar la cuenta Slurm y las rutas compartidas anunciadas para el curso, y el entorno conda personal creado siguiendo el capítulo de configuración. El CSV comprimido ATLAS y los datos CMS se leen desde allí. Guardar configuraciones, variables extraídas, registros y resultados únicamente en $HOME/hep-workshop de tu propia cuenta.

Los comandos de inicio están en [Configuración del sistema](../yuca-course/01_entorno.md), que es el primer capítulo de este mismo curso. No se requiere una cuenta CERN para leer estas muestras públicas. La práctica principal usa PyTorch con ROCm; el complemento CMS usa uproot/ROOT.

## Ruta de aprendizaje

- [Configuración del sistema: primer paso para el alumno](../yuca-course/01_entorno.md)
- [Práctica principal: ATLAS Higgs Challenge en GPU](atlas-gpu.md)
- [Complemento: clasificación CMS desde NanoAOD](higgs.md)
- [Exploración: autoencoder CMS](autoencoder.md)
- [Bitácora ATLAS: tablas por completar y preguntas](atlas-experiments.md)

Código en [`workshop/`, rama opendata_dev](https://github.com/castaned/ML-integration-CMSSW/tree/opendata_dev/workshop). Uso de cómputo de alto rendimiento: clúster ACARUS de la Universidad de Sonora.
