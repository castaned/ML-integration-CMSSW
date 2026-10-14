# Practical Machine Learning in HEP

Dos jornadas: miércoles de tres horas y jueves de una hora en el clúster Yuca: **clasificación de Higgs con CMS NanoAOD** y **detección de anomalías con CMS Open Data**. Cada equipo modifica un modelo, registra sus resultados y justifica una decisión física.

**Este es el curso Yuca Open Data, con el nombre Practical Machine Learning in HEP.** Es una única ruta de aprendizaje: configuración del sistema → datos abiertos → análisis de NanoAOD → extracción de observables → entrenamiento → evaluación.

## Empezar aquí

1. [Primer acceso SSH y activación de la cuenta con 2FA](../yuca-course/00_acceso.md), una sola vez y preferentemente antes del taller.
2. [Repositorio y entorno de trabajo](../yuca-course/01_entorno.md), con la cuenta ya activada.
3. [Datos abiertos, formato NanoAOD y revisión de archivos](../yuca-course/02_datos.md).
4. [Ejemplo 1: selección y reconstrucción Higgs/ZZ, observables y clasificación](higgs.md).
5. [Ejemplo 2: autoencoder CMS multileptónico](autoencoder.md).
6. [Modificaciones y bitácora de experimentos](experiments.md).

No empezar ejecutando entrenamientos: comprobar primero el entorno, las rutas compartidas y la lectura de Events. El instructor prepara dependencias y descargas antes de clase; cada alumno configura su sesión y su espacio de trabajo al inicio.

## Programa: miércoles y jueves

| Jornada | Distribución del tiempo | Producto del alumno |
| --- | --- | --- |
| Miércoles, hora 1 | 20 min acceso/entorno; 10 min Events; 30 min selección y extracción | Cutflow, masas reconstruidas y referencia |
| Miércoles, hora 2 | 15 min primer entrenamiento; 25 min una variación; 10 min test final; 10 min discusión | Comparación y evaluación final Higgs |
| Miércoles, hora 3 | 10 min anomalías; 10 min datos CMS; 25 min entrenamiento; 15 min diagnóstico | Referencia de autoencoder |
| Jueves, hora 1 | 10 min repaso; 25 min una variación; 15 min comparación; 10 min presentación | Tabla y conclusiones de cada equipo |

Las colas pueden afectar los tiempos: el instructor debe probar las asignaciones antes del taller y conservar resultados de referencia. No se garantiza un tiempo de entrenamiento universal. Cada equipo realiza una mejora; los ejercicios restantes son extensiones.

## Dos preguntas físicas

1. **Supervisado:** Higgs de 125 GeV→ZZ*→4 leptones frente a ZZ→4 leptones. Ambas muestras son NanoAODv9 UL16 de CMS. El alumno realiza la selección y construye masas y momentos antes de entrenar.
2. **No supervisado:** DYJets HT 70–100, WZ y ZZ de CMS como referencia electrodébil multileptónica; W′→WZ→3ℓν como referencia de evaluación.

Son simulaciones abiertas, no etiquetas de procesos medidas en colisiones reales. La práctica usa una selección educativa simplificada, no reproduce el análisis oficial CMS. El CSV ATLAS anterior queda como extensión opcional.

## Antes de empezar

El instructor comunica cuenta Slurm, entorno conda y dos rutas compartidas: carpeta de NanoAOD Higgs/ZZ y YAML de referencia del autoencoder CMS con rutas absolutas. Los alumnos leen esos datos y escriben únicamente en su propio HOME.

Los comandos de inicio están en [Configuración del sistema](../yuca-course/01_entorno.md), que es el primer capítulo de este mismo curso. No se requiere una cuenta CERN para leer estas muestras públicas. La práctica Higgs usa uproot para leer ROOT; el flujo de referencia del framework utiliza además PyROOT.

## Ruta de aprendizaje

- [Configuración del sistema: primer paso para el alumno](../yuca-course/01_entorno.md)
- [Preparación del instructor](instructor.md)
- [Miércoles, horas 1 y 2: Higgs frente a fondo](higgs.md)
- [Miércoles, hora 3, y jueves: autoencoder CMS](autoencoder.md)
- [Bitácora de experimentos](experiments.md)

Código en [`workshop/`, rama opendata_dev](https://github.com/castaned/ML-integration-CMSSW/tree/opendata_dev/workshop). Uso de cómputo de alto rendimiento: clúster ACARUS de la Universidad de Sonora.
