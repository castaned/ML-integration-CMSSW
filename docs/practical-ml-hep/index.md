# Practical Machine Learning in HEP

**Vamos a reconocer eventos de Higgs, diseñar redes y descubrir qué cambia cuando las entrenamos de otra forma.** Trabajaremos con CERN Open Data en el clúster Yuca de ACARUS, Universidad de Sonora.

La práctica principal es **ATLAS Higgs Challenge**. El autoencoder CMS será una exploración complementaria: otra red y otra pregunta física.

![Nuestro recorrido de datos a conclusiones](../assets/workshop/atlas_higgs_workflow.svg)

## Nuestro recorrido

<div class="grid cards" markdown>

- **1. Entender la física**

    ¿Qué señal buscamos? ¿Qué procesos la imitan? [Señal, fondos y las 30 variables](atlas-physics.md).

- **2. Probar una red**

    Cambia su arquitectura y aprendizaje desde un YAML. [Laboratorio ATLAS](atlas-gpu.md).

- **3. Observar y comparar**

    Mira curvas, registra números y contrasta tu hipótesis. [Bitácora breve](atlas-experiments.md).

- **4. Explicar lo aprendido**

    Comparte una figura y una conclusión con el salón. [Puesta en común](delivery.md).

</div>

## Cómo participaremos

Trabajaremos individualmente o en grupos cercanos, según la disposición del salón. Todos comenzamos con una red de referencia. Cada grupo prueba al menos un cambio y comparte qué ocurrió. Si hay tiempo, hacemos una segunda prueba.

**No necesitas editar Python ni los scripts de Yuca.** Tu herramienta de experimentación es el YAML. Cada entrenamiento guarda sus resultados en una carpeta personal diferente. Los datos ya están en una carpeta compartida.

| Momento | Pregunta central |
| --- | --- |
| Inicio | ¿Qué información permite distinguir Higgs y fondo? |
| Primer entrenamiento | ¿Cómo sabemos si la red está aprendiendo? |
| Variaciones | ¿Qué cambió al aumentar capas, cambiar aprendizaje o dropout? |
| Comparación CPU–GPU | ¿Cuánto tiempo cuesta el mismo entrenamiento? |
| Cierre | ¿Qué podemos concluir con nuestros resultados? |

El taller tiene tres horas el miércoles y una el jueves. Ajustaremos las pruebas al ritmo del grupo; buscamos comprender una comparación, no acumular entrenamientos.

??? info "Antes de la sesión: acceso y ambiente"
    Completa el [primer acceso y activación de 2FA](../yuca-course/00_acceso.md) y la [preparación de tu cuenta](../yuca-course/01_entorno.md). Para ATLAS se usa el [ambiente GPU preparado para Yuca](atlas-reference.md#entorno-gpu-de-yuca). Estas tareas se hacen una sola vez y se revisan con apoyo si hay dificultades.

## Para seguir explorando

- [Autoencoder CMS: otra motivación para una red neuronal](autoencoder.md).
- [Complemento: análisis desde NanoAOD de CMS](higgs.md).
- [Apoyo de comandos y archivos](atlas-howto.md).
- [Detalles del método y benchmarks históricos](atlas-reference.md).

Código y configuraciones en el [repositorio del taller](https://github.com/castaned/ML-integration-CMSSW/tree/opendata_dev/workshop). Este es un único curso: **Practical Machine Learning in HEP / Yuca Open Data**.
