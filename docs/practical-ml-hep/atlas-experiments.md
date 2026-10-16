# Bitácora: experimenta, registra y concluye

**Grupo:** __________ · **Participantes:** __________ · **Fecha:** __________

Copien estas tablas a su documento compartido. Completen las filas durante el taller: no esperen hasta el final. Si una corrida falla o no mejora, registren también lo que aprendieron. Para cada corrida conserven un YAML y una carpeta de resultados distintos.

[Volver a los pasos del laboratorio](atlas-gpu.md)

## Antes de entrenar: ¿qué información tenemos? {#antes-de-entrenar-que-informacion-tenemos}

Elijan tres variables de las imágenes generadas con el YAML y consulten su significado en el [registro CERN](https://opendata.cern.ch/record/328).

| Variable | ¿Qué mide? | ¿Señal y fondo se parecen? | ¿Esperamos que ayude? ¿Por qué? |
| --- | --- | --- | --- |
| | | | |
| | | | |
| | | | |

**Para discutir:** ¿podemos decidir solo mirando una variable? ¿Qué podría aportar combinar varias? ¿Un valor ausente siempre indica un error, o puede significar que no hay un jet en ese evento?

## Primera corrida: nuestra referencia

Lean `metrics.json` y miren `training_summary.png`. La curva y los números corresponden al mejor modelo guardado.

| YAML | Carpeta de resultados | Capas ocultas | Dropout | Aprendizaje | Lote | Mejor época | Épocas ejecutadas | Tiempo (s) | AUC | AMS interna |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | | | |

**Preguntas:** ¿la red separa señal y fondo? ¿En qué se nota? ¿Bajan ambas pérdidas? ¿El mejor modelo coincide con la última época? ¿Qué guardamos para poder reproducir la corrida?

## Nuestro experimento: cambia una idea

**Hipótesis antes de entrenar:** Si cambiamos __________, esperamos __________ porque __________.

| Corrida | Único parámetro que cambió | Valor anterior → nuevo | Carpeta nueva | AUC | AMS interna | Tiempo (s) |
| --- | --- | --- | --- | --- | --- | --- |
| Referencia | Ninguno | | | | | |
| Variación 1 | | | | | | |
| Variación 2 | | | | | | |

| Comparación con referencia | ¿Qué mejoró? | ¿Qué empeoró o costó más? | ¿Nuestra hipótesis se sostuvo? |
| --- | --- | --- | --- |
| Variación 1 | | | |
| Variación 2 | | | |

**Para discutir:** ¿más capas o neuronas siempre ayudan? ¿AUC y AMS cambiaron en la misma dirección? ¿Podemos atribuir una diferencia pequeña a una mejora real con una sola corrida? ¿Qué deberíamos repetir?

## Entrenar más y saber cuándo parar

Para el grupo que pruebe `epochs: 200` y `patience: 15`, registrar:

| Corrida | Máximo de épocas | Paciencia | Mejor época | Épocas ejecutadas | ¿Qué hacen las dos pérdidas después de la mejor época? |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

**Preguntas:** ¿por qué puede parar antes del máximo? ¿Por qué la pérdida de entrenamiento puede bajar mientras validación empeora? ¿Qué modelo se usa para calcular la ROC? ¿Cambiar dropout modifica ese comportamiento?

**Conclusión:** En nuestra corrida observamos __________. La parada temprana permitió __________.

## CPU frente a GPU

Usen la misma arquitectura, lote, datos y número de épocas. Si la parada temprana produce duraciones distintas, indíquenlo y no atribuyan toda la diferencia al dispositivo.

| Arquitectura | Épocas CPU / GPU | Tiempo CPU (s) | Tiempo GPU (s) | Aceleración CPU/GPU | AUC CPU / GPU | AMS CPU / GPU |
| --- | --- | --- | --- | --- | --- | --- |
| Inicial | | | | | | |
| Mayor | | | | | | |

**Cálculo:** aceleración = tiempo CPU ÷ tiempo GPU. Un valor mayor que 1 indica que GPU fue más rápida.

**Preguntas:** ¿la ventaja de GPU cambia al aumentar la red? ¿GPU implica una mejor clasificación o principalmente otro tiempo de cálculo? ¿Incluyen nuestros tiempos la espera en cola? ¿Bastan estas corridas para asegurar una aceleración universal?

**Conclusión:** Para la red __________, observamos una aceleración de __________. La interpretación que podemos defender es __________.

## Referencia externa: el challenge original {#referencia-externa-el-challenge-original}

Estos números vienen del conjunto privado del challenge, según la [tabla 2 de la publicación original](https://proceedings.mlr.press/v42/cowa14.pdf):

| Referencia histórica | AMS privada |
| --- | ---: |
| TMVA | 3.19956 |
| MultiBoost | 3.40488 |
| Ganador: conjunto de redes profundas | 3.80581 |

Mantener separada la comparación del curso:

| Nuestro modelo elegido | AUC interna | AMS interna | AMS privada independiente | ¿Es directamente comparable con la tabla histórica? |
| --- | --- | --- | --- | --- |
| | | | Pendiente | Todavía no: nuestra evaluación es interna |

**Preguntas:** ¿qué diferencia hay entre validación y evaluación final? ¿Por qué no basta con que nuestra AMS interna sea mayor que 3.40? ¿Podemos elegir el umbral mirando los resultados privados y seguir llamándolos una prueba independiente?

La primera versión del laboratorio no calcula la AMS privada. No inventar ese valor ni usar la AMS interna para asignarse una posición en la competición. Comparar con rigor incluye reconocer qué mediciones faltan.

## De una mejor ROC a una pregunta de física

Leer el [ejemplo físico](atlas-physics.md#ejemplo-para-completar-en-clase). Partimos de rendimientos **hipotéticos** de 100 señales y 10 000 fondos. Completar sin usar un entrenamiento:

| Selección | Señal conservada | Fondo aceptado | s esperado | b esperado | s / √b aproximado |
| --- | --- | --- | --- | --- | --- |
| A | 60% | 10% | | | |
| B | 60% | 5% | | | |

**Preguntas:** ¿qué selección corresponde al punto más favorable de la ROC? ¿Cambió la sección eficaz del Higgs o nuestra capacidad de aislarlo? ¿Por qué no podemos calcular un límite real solo con la AUC?

Después conectar con nuestros entrenamientos:

| Corrida elegida | ¿En qué zona de la ROC nos interesa mejorar? | ¿Preferimos conservar señal o reducir fondo? ¿Por qué? | ¿Qué información falta para medir σ o calcular un límite? |
| --- | --- | --- | --- |
| | | | |

La ROC del taller no tiene pesos. Para rendimientos físicos se suman los pesos de los eventos seleccionados; no basta con contar eventos simulados. La comparación final debe considerar incertidumbres y conservar una evaluación independiente.

## Cierre: tres frases por grupo

1. **Probamos:** __________.
2. **Observamos:** __________, con AUC __________, AMS interna __________ y tiempo __________.
3. **Concluimos:** __________. Para comprobarlo mejor, repetiríamos __________.

Compartir la bitácora, los YAML, `metrics.json` y una gráfica representativa de cada comparación. Los resultados de referencia medidos por el docente están en el [anexo opcional](atlas-reference.md#experimentos-de-referencia-medidos-en-yuca): consultarlos después de registrar sus propias observaciones.
