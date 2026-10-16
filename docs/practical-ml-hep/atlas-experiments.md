# Bitácora breve del grupo

**Grupo o mesa:** __________ · **Participantes:** __________

Completen esta página en su documento compartido **mientras experimentan**. Basta una comparación bien entendida; una segunda prueba es opcional.

## Antes de entrenar: ¿qué información tenemos? {#antes-de-entrenar-que-informacion-tenemos}

Elijan una variable de las [treinta entradas](atlas-physics.md#las-30-variables-organizadas-por-su-significado):

**La variable __________ representa __________. En su gráfica señal y fondo __________. Creemos que podría ayudar porque __________.**

## Nuestra hipótesis

**Cambiaremos __________ de __________ a __________. Esperamos __________ porque __________.**

Copien el YAML y elijan una carpeta nueva antes de modificarlo. Mantengan iguales los datos de ambas corridas.

## Nuestros resultados

| Corrida | ¿Qué cambió? | AUC | AMS interna | Tiempo (s) | ¿Qué muestran las curvas? |
| --- | --- | --- | --- | --- | --- |
| Referencia | Nada | | | | |
| Variación | | | | | |
| Segunda prueba, opcional | | | | | |

**Carpetas de referencia y variación:** __________ / __________.

## Nuestra interpretación

1. ¿Se cumplió lo que esperábamos? ¿Qué número o curva lo respalda?
2. ¿Mejoraron AUC y AMS juntas? Si no, ¿cómo lo interpretaríamos?
3. ¿La pérdida de validación acompaña a la de entrenamiento o empieza a empeorar?
4. ¿El tiempo adicional justificó lo que obtuvimos?

**Nuestra conclusión en dos frases:** __________.

??? question "Si hay tiempo: CPU frente a GPU"
    Comparen la misma red y el mismo número de épocas. Registren el tiempo de cálculo, no la espera en cola.

    | Red | Tiempo CPU (s) | Tiempo GPU (s) | CPU/GPU | ¿Qué aprendimos? |
    | --- | --- | --- | --- | --- |
    | | | | | |

    ¿La GPU cambió principalmente el tiempo o también el resultado? ¿Podemos generalizar a cualquier red con una sola prueba?

## Referencia externa: el challenge original {#referencia-externa-el-challenge-original}

Los benchmarks publicados son **AMS 3.40 (MultiBoost)** y **3.81 (ganador)**. Nuestra AMS interna no se compara directamente: todavía no hemos realizado la evaluación privada independiente.

**Pregunta:** ¿qué tendríamos que mantener independiente antes de afirmar que superamos un benchmark? [Contexto y fuente de los números](atlas-reference.md#benchmarks-publicados-del-higgs-challenge).

[Compartir nuestra comparación](delivery.md) · [Más preguntas opcionales](atlas-experiments-reference.md)
