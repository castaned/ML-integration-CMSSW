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

Los ejercicios de selección de eventos y retirada de variables del capítulo Higgs son extensiones. No mezclarlos con los cuatro escenarios controlados: cambiarían además los datos o las entradas.

## Generar los YAML de cada grupo

Después de preparar el YAML que apunta a la extracción personal Higgs:

```bash
python workshop/setup_groups.py --task higgs \
  --reference "$HOME/hep-workshop/configs/classifier.yaml" \
  --config-dir "$HOME/hep-workshop/configs/groups_higgs_$USER" \
  --results-root "$HOME/hep-workshop/results/groups_higgs"
```

Este paso establece una referencia **MLP**, aunque el primer ejercicio haya usado regresión logística. No comparar la variación MLP con una referencia logística: ejecutar la referencia MLP generada. Se crean dos archivos por grupo: `higgs_group1_baseline.yaml` y `higgs_group1_variation.yaml`, y equivalentes para grupos 2–4.

Para CMS, a partir del YAML personal previamente verificado:

```bash
python workshop/setup_groups.py --task autoencoder \
  --reference "$HOME/hep-workshop/configs/ae_baseline.yaml" \
  --config-dir "$HOME/hep-workshop/configs/groups_ae_$USER" \
  --results-root "$HOME/hep-workshop/results/groups_ae"
```

Cada alumno ejecuta **solo los dos YAML del grupo asignado**. No son dieciséis entrenamientos por alumno. El generador preserva datos y particiones, asigna salidas nuevas y guarda el escenario en `workshop`. No editar los metadatos de esa sección.

Ejemplo grupo 1, desde la raíz del repositorio:

```bash
sbatch --account=CUENTA_DEL_CURSO --output="$HOME/hep-workshop/logs/%j.out" \
  workshop/run_cpu.slurm higgs \
  "$HOME/hep-workshop/configs/groups_higgs_$USER/higgs_group1_baseline.yaml" \
  "$HOME/hep-workshop/results/groups_higgs/higgs_group1_baseline"
```

Repetir con `variation` en las dos rutas. Para autoencoder usar el modo `autoencoder` y el YAML `autoencoder_group1_baseline.yaml` o `variation`; la salida se toma del propio YAML. Mantener todos los resultados anteriores.

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
python workshop/collect_results.py \
  --config-dirs "$HOME/hep-workshop/configs/groups_higgs_$USER" "$HOME/hep-workshop/configs/groups_ae_$USER" \
  --output "$HOME/hep-workshop/comparacion.csv"
```

El CSV incluye tareas pendientes y deltas respecto a la referencia. Rechaza parejas que difieren en más parámetros/datos/semilla que lo asignado, y excluye resultados de test Higgs. Usar un nombre nuevo al actualizar la tabla; no sobrescribe archivos.

Cada grupo comparte su CSV y sus dos configuraciones. El instructor puede reunir los CSV en una hoja común; para recopilar directamente desde YAML de varios alumnos, las carpetas deben tener nombres únicos y sus rutas de resultados deben ser accesibles. No abrir permisos generales del HOME para hacerlo.

## Documento de conclusiones

Cada grupo completa estas cuatro frases en un documento común:

1. Nuestra hipótesis era…
2. Cambiamos únicamente… y observamos… frente a la referencia.
3. El coste en tiempo/iteraciones fue…
4. No podemos concluir… porque…

Cierre del curso: ¿qué configuración elegiríamos y por qué?, ¿vale la pena su coste?, ¿qué se repetiría con más semillas o datos? Una variación que no mejora también es un resultado útil si se interpreta y documenta.
