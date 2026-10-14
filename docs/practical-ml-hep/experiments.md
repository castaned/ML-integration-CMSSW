# Laboratorio en cuatro grupos: modificar YAML y comparar

El objetivo es explicar **qué cambió, qué mejoró y con qué coste**, no encontrar una red ganadora a cualquier precio. Dividir a los participantes en cuatro grupos. Cada grupo ejecuta una referencia común y una variación asignada; después reúne sus resultados con los demás.

## Cuatro escenarios

| Grupo | Pregunta | Clasificador neuronal Higgs | Autoencoder CMS |
| --- | --- | --- | --- |
| 1. Capacidad | ¿Más neuronas ayudan? | hidden_dims: [32,16] → [64,32] | hidden_dims: [16,8] → [32,16] |
| 2. Aprendizaje | ¿Un paso menor mejora el ajuste? | learning_rate: 0.001 → 0.0003 | learning_rate: 0.001 → 0.0003 |
| 3. Lotes | ¿Cómo afecta el tamaño del batch? | batch_size: 128 → 256 | batch_size: 256 → 128 |
| 4. Entrenamiento/compresión | ¿Qué aporta más ajuste o menor compresión? | max_iter: 100 → 200 | latent_dim: 2 → 4 |

`max_iter` y `epochs` son límites: la parada temprana puede finalizar antes. Registrar también iteraciones realmente ejecutadas. En cada práctica se cambia **un único parámetro**; el escenario 4 estudia cuestiones distintas en clasificación y reconstrucción.

## Condiciones comunes

- Misma extracción NanoAOD, observables, cantidad de eventos y semilla 16 en clasificación.
- Mismos HDF5, observables, particiones y semilla en autoencoder.
- Mismo umbral de aceptación nominal: 10% de fondo en clasificación y percentil 99 SM en autoencoder.
- Recursos Slurm iguales; registrar el tiempo como medida orientativa, no como benchmark de hardware.
- Elegir parámetros con validación. El test Higgs se consulta una vez tras cerrar la comparación. La referencia W′ se discute al final como evaluación exploratoria y no se usa para elegir la red.

La selección y los observables son comunes. Durante este ejercicio no se cambian: la comparación estudia únicamente parámetros de la red.

## Trabajar solamente con el YAML de variación

La preparación del entorno ya generó los archivos de tu grupo. Consultar sus ubicaciones:

```bash
python workshop/student.py files
```

En **Files** de Open OnDemand, abrir el YAML de `variation`, revisar el bloque `model`, cambiar solo el campo asignado y guardar. Los valores de la tabla son la propuesta de variación; no editar el YAML de `baseline`.

| Sección | Acción del alumno |
| --- | --- |
| model, parámetro asignado | Editar en el YAML de variación |
| model, otros campos | Mantener la referencia común |
| data / split / evaluation / anomaly_detection | No modificar |
| workshop / rutas / etiquetas | No modificar |
| Python / Slurm | Ejecutar sin editar |

Ejemplo del campo que cambia el grupo 2:

```yaml
model:
  learning_rate: 0.0003
```

Esta muestra es solo un fragmento: conservar el resto de tu YAML. No reemplazarlo por este fragmento.

Enviar los entrenamientos sin cambiar cuentas ni rutas en los comandos:

```bash
python workshop/student.py train --task higgs --role baseline
python workshop/student.py train --task higgs --role variation
```

Para la segunda práctica cambiar únicamente el nombre de tarea indicado en los comandos:

```bash
python workshop/student.py train --task autoencoder --role baseline
python workshop/student.py train --task autoencoder --role variation
```

Cada práctica requiere referencia y variación, no todos los escenarios. La interfaz impide cambiar datos o parámetros ajenos al escenario. No repetir un entrenamiento encima de sus resultados; conservarlos para la comparación.

## Tabla común para el cierre

[Descargar plantilla CSV para Google Sheets](../assets/workshop/tabla_comparacion.csv). Puede importarse a Sheets o utilizarse como tabla de trabajo junto a un documento de conclusiones.

| Equipo | Práctica | Cambio | Referencia | Variación | Diferencia | Tiempo | Interpretación |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Higgs / AE | Capacidad | | | | | |
| 2 | Higgs / AE | Aprendizaje | | | | | |
| 3 | Higgs / AE | Lote | | | | | |
| 4 | Higgs / AE | Iteraciones / latente | | | | | |

**Clasificación:** métrica principal AUC de validación (mayor es mejor), complementada con eficiencia Higgs a la aceptación de fondo fijada. Registrar tiempo e iteraciones.

**Autoencoder:** métrica principal mejor pérdida de validación SM (menor es mejor), complementada con épocas y tiempo. Una pérdida menor significa mejor reconstrucción SM, **no necesariamente mayor sensibilidad a anomalías**. La aceptación SM en test se conserva como diagnóstico; la tabla automática no compara AUC W′ ni eficiencia W′ para elegir parámetros.

Diferencia = variación − referencia. Por tanto, una diferencia positiva de AUC favorece la variación; una diferencia negativa de pérdida SM favorece su reconstrucción. Estos cambios con una semilla son observaciones del taller, no mejoras estadísticamente demostradas.

## Reunir valores automáticamente

Después de terminar los trabajos:

```bash
python workshop/student.py collect
```

El CSV incluye tareas pendientes y deltas respecto a la referencia. Rechaza parejas que difieren en más parámetros/datos/semilla que lo asignado, y excluye resultados de test Higgs. La interfaz crea automáticamente un nombre nuevo con fecha y hora; no sobrescribe archivos.

Cada grupo comparte su CSV y sus dos configuraciones. Compartir únicamente el CSV y las configuraciones solicitadas para completar la tabla común. No es necesario compartir permisos de tu HOME ni copiar datasets.

## Documento de conclusiones

Cada grupo completa estas cuatro frases en un documento común:

1. Nuestra hipótesis era…
2. Cambiamos únicamente… y observamos… frente a la referencia.
3. El coste en tiempo/iteraciones fue…
4. No podemos concluir… porque…

Cierre del curso: ¿qué configuración elegiríamos y por qué?, ¿vale la pena su coste?, ¿qué se repetiría con más semillas o datos? Una variación que no mejora también es un resultado útil si se interpreta y documenta.


## Compartir los resultados del grupo

Continuar con [Entrega y comparación colectiva](delivery.md): generar el paquete, subir pocas figuras representativas a la carpeta compartida del curso y completar la hoja Higgs o autoencoder. Los entrenamientos permanecen en tu cuenta; solo se comparte la selección de resultados.
