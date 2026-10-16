# Laboratorio ATLAS: cambia, observa y explica

**Tu misión:** probar una idea sobre una red neuronal y explicar qué ocurrió usando sus curvas y resultados.

## Entender el problema

Queremos separar **Higgs → ττ** de procesos de fondo que pueden producir objetos similares. La red recibe **30 variables físicas** y asigna una puntuación a cada evento.

![Higgs a dos taus: leptón, hadrones y tres neutrinos](../assets/workshop/higgs_tautau_final_state.svg)

*Cadena ilustrativa del taller: esperamos un electrón o muón, un tau hadrónico y momento transversal faltante por los tres neutrinos. También se considera el conjugado de carga. [Ver la explicación del diagrama](atlas-physics.md#el-estado-final-que-buscamos).*

Antes de entrenar, conversamos: **¿qué distingue señal y fondo? ¿Por qué los neutrinos dificultan reconstruir el Higgs?** La [introducción física](atlas-physics.md) explica las muestras y las 30 variables, no solo las que aparecen en esta imagen:

![Seis ejemplos de las treinta variables](../assets/workshop/atlas_variables_01.png)

*Cada curva permite comparar formas de señal y fondo. Este panel muestra seis variables; la red utiliza las treinta.*

## Preparar una referencia común

Primero ejecutaremos todos la misma configuración. Los datos ya están compartidos en Yuca y cada cuenta guarda sus propios resultados.

??? info "Comandos de preparación: una sola vez"
    Con el acceso y el ambiente GPU ya preparados, ejecutar desde la terminal:

    ```bash
    cd "$HOME/ML-integration-CMSSW"
    git pull --ff-only origin opendata_dev
    mkdir -p "$HOME/hep-workshop/configs" "$HOME/hep-workshop/logs"
    cp -n workshop/configs/atlas_higgs_gpu.yaml "$HOME/hep-workshop/configs/atlas_baseline01.yaml"
    ```

    Si falta configurar tu cuenta, consulta el [apoyo de preparación](atlas-reference.md#entorno-gpu-de-yuca). Para generar las comparaciones de las treinta variables, sigue el [apoyo de visualización](atlas-howto.md#3-mira-las-variables-antes-de-entrenar).

## Tu herramienta: el YAML

Abre `hep-workshop/configs/atlas_baseline01.yaml` con el editor de **Files de Open OnDemand**. Al principio conserva la configuración de referencia.

| Campo que puedes cambiar | Idea que estás probando |
| --- | --- |
| `hidden_dims` | Número de capas y neuronas por capa |
| `dropout` | Regularización para evitar aprender demasiado los detalles del entrenamiento |
| `learning_rate` | Tamaño de los pasos al aprender |
| `batch_size` | Cuántos eventos procesa juntos |
| `epochs` y `patience` | Cuánto puede entrenar y cuándo dejar de insistir |

**Ejemplo dentro del YAML:**

```yaml
model:
  hidden_dims: [128, 64, 32, 16]
  dropout: 0.1
```

Son cuatro capas ocultas. Para ensayar una red mayor, podrías cambiar solo la lista a `[512, 256, 128, 64]`. No necesitas modificar el código ni los scripts del clúster.

## Un experimento, una carpeta

**Antes de modificar la referencia, copia su YAML con otro nombre.** Por ejemplo, `atlas_02.yaml`. Dentro de esa copia cambia una idea y elige una carpeta nueva:

```yaml
output:
  directory: $HOME/hep-workshop/results/atlas_02
```

Conserva el resto del archivo. Cambiar el nombre del YAML no cambia por sí solo la carpeta de salida. Los resultados anteriores se conservan para poder compararlos.

| Experimento | Qué queremos averiguar |
| --- | --- |
| Más neuronas o capas | ¿Aprende mejor o solo se vuelve más complejo? |
| Otro aprendizaje | ¿Cambia cómo progresa la red? |
| Más dropout | ¿Mejora su comportamiento en eventos que no usó para aprender? |
| Más épocas con parada temprana | ¿Cuándo deja de mejorar? |

**Antes de enviar, escribe una frase:** «Esperamos que este cambio… porque…».

??? info "Cómo copiar y enviar un YAML"
    Copiar la referencia, editar la copia en Files y cambiar su carpeta de salida:

    ```bash
    cp -n "$HOME/hep-workshop/configs/atlas_baseline01.yaml" "$HOME/hep-workshop/configs/atlas_02.yaml"
    ```

    Desde la raíz del repositorio, enviar el YAML elegido. Para la referencia, usar `atlas_baseline01.yaml` en la última línea:

    ```bash
    sbatch --output="$HOME/hep-workshop/logs/atlas_%j.out" \
      workshop/run_atlas_gpu.slurm "$HOME/hep-workshop/configs/atlas_02.yaml"
    squeue -u "$USER"
    ```

    Si hay un problema con el trabajo, consulta el [apoyo de comandos y archivos](atlas-howto.md). Los fragmentos YAML se editan dentro del archivo; no se ejecutan en la terminal.

## Ahora mira lo que ocurrió

Abre **`training_summary.png`** en la carpeta de tu corrida. Los números para la tabla están en **`metrics.json`**.

| Observa | Interpreta |
| --- | --- |
| Pérdida de entrenamiento y validación | ¿Aprende también sobre eventos que no vio al entrenar? |
| Curva ROC | ¿Conserva más señal para el mismo fondo aceptado? |
| Puntuaciones de señal y fondo | ¿Dónde se separan y dónde se confunden? |
| AUC y AMS interna | ¿Mejoró la separación global y también la selección? |
| Tiempo y épocas | ¿La mejora justificó el costo? |

Una curva de validación que empeora mientras entrenamiento sigue mejorando sugiere **sobreajuste**. La parada temprana conserva el modelo con menor pérdida de validación. Una red más grande o más tiempo no garantizan mejores resultados.

Una mejor selección puede ayudar a medir procesos o aumentar la sensibilidad a señales. No cambia la sección eficaz física ni calcula por sí sola un límite: [explicación con un ejemplo](atlas-physics.md#leer-una-roc-como-fisico).

## Comparar y conversar

Completa la **[bitácora breve](atlas-experiments.md)** durante la actividad. Compara con la referencia usando los mismos datos y cambiando una idea cada vez. Si hay tiempo, prueba una segunda variación o compara CPU y GPU con apoyo del docente.

Al cerrar, comparte una figura y responde: **¿qué esperabas, qué observaste y qué puedes concluir?** [Puesta en común](delivery.md).

Nuestra AMS es de validación interna. Los números históricos del challenge corresponden a otra evaluación; se consultan como [referencia externa](atlas-reference.md#benchmarks-publicados-del-higgs-challenge), no como una clasificación directa de nuestros grupos.

[Apoyo operativo](atlas-howto.md) · [Física y todas las variables](atlas-physics.md) · [Detalles opcionales del método](atlas-reference.md)
