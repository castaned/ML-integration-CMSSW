# Práctica 2: anomalías con CMS

## Miércoles, tercera hora: aprender la referencia del Modelo Estándar

El autoencoder aprende eventos multileptónicos asociados al sector electrodébil del SM, usando DYJets HT 70–100, WZ y ZZ. W′→WZ→3ℓν, de 1 TeV, se usa como referencia de nueva física **solo para evaluación**. Las muestras son simulaciones abiertas CMS; no se entrena con W′.

### 1. De NanoAOD a una configuración personal (10 min)

La selección de tres leptones del repositorio produce candidatos Z/W y observables por canal. Revisar `example_files/main_process/filterNanoAOD.py`, las ramas de entrada, la selección y su cutflow. El flujo original y sus comandos Slurm se encuentran en [procesamiento NanoAOD](../yuca-course/03_procesamiento.md). Por el límite de cuatro horas, cada equipo procesa NanoAOD en la práctica Higgs; en autoencoder se reutiliza el HDF5 obtenido con el flujo CMS ya validado. Reprocesar un archivo WZ es una extensión, no confundir ese HDF5 con datos de origen.


Utilizar el YAML de referencia disponible en la carpeta compartida, con las rutas absolutas de los HDF5 del curso. No sustituirlas por rutas del HOME del alumno.

```bash
python workshop/setup_autoencoder.py \
  --reference /RUTA/COMPARTIDA/autoencoder_reference.yaml \
  --config "$HOME/hep-workshop/configs/ae_baseline.yaml" \
  --results "$HOME/hep-workshop/results/ae_baseline"
python scripts/check_dyjets_ht_pilot.py \
  -f "$HOME/hep-workshop/configs/ae_baseline.yaml"
```

El generador verifica que las entradas sean accesibles, cambia solamente la salida personal y desactiva la exportación ONNX para simplificar la práctica. La biblioteca ONNX sigue siendo dependencia del módulo existente.

### 2. Entrenar (25 min)

```bash
sbatch --account=CUENTA_DEL_CURSO \
  --output="$HOME/hep-workshop/logs/%j.out" \
  workshop/run_cpu.slurm autoencoder \
  "$HOME/hep-workshop/configs/ae_baseline.yaml"
```

La arquitectura inicial es 10→16→8→2→8→16→10. Entradas: MET_pt, M3l, Z_deltaR, Z_mass, Lep_pt_sum, Z_pt, Lep1Z_pt, Lep2Z_pt, Lep3W_pt y W_mt. Son variables del canal seleccionado; Dataset_ID sirve para separar muestras y nunca es una entrada de la red.

Se minimiza MSE con Adam. El escalado se aprende únicamente del entrenamiento SM, balanceando procesos. El umbral es el percentil 99 de validación SM con igual peso por proceso. Consultar el YAML guardado para los parámetros exactos.

### 3. Diagnóstico (15 min)

Abrir `loss_workshop_autoencoder.pdf` y `scores_by_process_workshop_autoencoder.pdf`; revisar los archivos de métricas y el registro Slurm. Comparar pérdidas de entrenamiento y validación. ¿Las dos siguen bajando? ¿El error significa automáticamente nueva física? ¿Puede reflejar ausencia de representatividad del fondo?

El ejecutor actual también produce ROC y eficiencia W′ al finalizar. **No usar esas cifras para escoger arquitectura o variables.** Guardarlas para la discusión final; si se inspeccionan repetidamente, tratar todo el estudio como exploratorio. El taller no dispone de una nueva muestra W′ independiente para confirmar elecciones.

## Jueves: variar, comparar y explicar

La actividad principal usa los [cuatro grupos YAML y la tabla común](experiments.md). Cada equipo ejecuta referencia y variación asignada; el escenario 4 estudia la dimensión latente. Los cambios sugeridos a continuación son extensiones.

Copiar el YAML de referencia y cambiar `data.output_path` a una carpeta nueva, por ejemplo `results/ae_latent4`. Elegir una única modificación:

| Ejercicio | Parámetro | Discusión |
| --- | --- | --- |
| Compresión | `model.latent_dim: 4` en lugar de 2 | ¿Reconstruye mejor SM? ¿Un error menor favorece necesariamente anomalías? |
| Capacidad | `model.hidden_dims: [32, 16]` | ¿Hay mejora en validación o solo entrenamiento? |
| Entrenamiento | `model.learning_rate: 0.0005` | ¿La curva baja más despacio o es más estable? |
| Umbral | `anomaly_detection.normal_quantile: 0.95` | ¿Qué aceptación SM esperas nominalmente? |

Mantener semilla y particiones para comparar. Una variación de semilla es una extensión de estabilidad; cambia las particiones y debe declararse. Nunca reutilizar una carpeta de resultados existente.

Registrar pérdida de validación, umbral y aceptación SM por proceso. Después discutir la referencia W′, declarando el carácter exploratorio. Si se estudian variables, verificar que estén presentes en todas las muestras y que la dimensión latente sea menor que el número de entradas.

## Limitaciones que deben aparecer en la entrega

- DYJets tiene poca estadística en el piloto anterior (49/17/17); el preflight confirma los conteos efectivos del conjunto compartido. No asumir que las cifras históricas se repiten tras cambiar los archivos.
- Pesos iguales por proceso no representan tasas por luminosidad; no son una predicción de fondo físico.
- Una sola masa/canal W′ no demuestra sensibilidad universal a nueva física.
- Una fluctuación o un evento mal reconstruido no constituye descubrimiento.

**Entrega:** configuración de referencia y variación, dos curvas de pérdida, tabla de métricas SM y una conclusión de tres frases. Agradecer el uso del clúster de alto rendimiento ACARUS de la UNISON.
