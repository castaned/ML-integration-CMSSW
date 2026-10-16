# Compartamos lo que aprendimos

**Cada grupo cuenta un pequeño experimento: qué esperaba, qué cambió y qué observó.** No buscamos entregar muchos archivos ni encontrar una red ganadora a toda costa.

## 1. Elijan una comparación

Comparen la red inicial con una variación que les parezca interesante. Puede haber mejorado, empeorado o dado prácticamente lo mismo: los tres resultados sirven para discutir.

## 2. Completen su fila

Copien esta tabla al documento compartido que se indique durante la sesión. Pueden trabajar por mesas o grupos cercanos.

| Grupo | ¿Qué cambiamos? | AUC antes → después | AMS interna antes → después | Tiempo antes → después | ¿Qué aprendimos? |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

Los números están en `metrics.json`, dentro de cada carpeta de resultados. Mantengan los mismos datos para comparar las redes. La AMS del curso es de validación interna; no equivale todavía a la evaluación privada del challenge.

## 3. Compartan una figura y sus configuraciones

En la carpeta compartida indicada en clase, suban:

- **Una o dos figuras** `training_summary.png` que permitan explicar la comparación.
- **Los dos YAML** utilizados, para poder repetirla.
- **La fila de resultados y su conclusión.** Pueden añadir los `metrics.json` para conservar los números.

Cada grupo usa su propio espacio, sin modificar las entregas de los demás. No hace falta subir datos originales, modelos completos, todos los registros ni preparar un archivo comprimido.

## 4. Expliquen su resultado en un minuto

Completen estas tres frases:

1. **Esperábamos que…**
2. **Al cambiar… observamos…**
3. **Por eso concluimos…; para comprobarlo mejor haríamos…**

Para conversar entre todos: ¿una red más grande siempre ayudó? ¿AUC y AMS mejoraron juntas? ¿La GPU cambió la calidad de la clasificación o principalmente el tiempo? ¿Las curvas muestran que entrenar más dejó de ayudar?

!!! tip "Lo importante es la explicación"
    Una comparación bien interpretada vale aunque el número no mejore. Diferencias pequeñas en una sola corrida no bastan para declarar un ganador.

La práctica principal es **ATLAS Higgs Challenge**. Si exploraron el autoencoder, comenten qué cambió en su objetivo y en el significado de la salida; no mezclen sus métricas en la tabla de clasificación.

[Volver al laboratorio](atlas-gpu.md) · [Bitácora breve del grupo](atlas-experiments.md) · [Referencias y benchmarks publicados](atlas-reference.md#benchmarks-publicados-del-higgs-challenge)
