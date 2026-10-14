# Práctica 2: anomalías con CMS

## Miércoles, tercera hora: aprender la referencia del Modelo Estándar

El autoencoder aprende eventos multileptónicos asociados al sector electrodébil del SM, usando DYJets HT 70–100, WZ y ZZ. W′→WZ→3ℓν, de 1 TeV, se usa como referencia de nueva física **solo para evaluación**. Las muestras son simulaciones abiertas CMS; no se entrena con W′.

### 1. De NanoAOD a una configuración personal (10 min)

La selección de tres leptones del repositorio produce candidatos Z/W y observables por canal. Revisar `example_files/main_process/filterNanoAOD.py`, las ramas de entrada, la selección y su cutflow. El flujo original y sus comandos Slurm se encuentran en [procesamiento NanoAOD](../yuca-course/03_procesamiento.md). Por el límite de cuatro horas, cada equipo procesa NanoAOD en la práctica Higgs; en autoencoder se reutiliza el HDF5 obtenido con el flujo CMS ya validado. Reprocesar un archivo WZ es una extensión, no confundir ese HDF5 con datos de origen.


Los datos compartidos y tu salida personal ya quedaron registrados en los YAML durante la preparación del entorno. Revisar las variables y la selección descritas aquí; no editar sus rutas ni los scripts.

### 2. Entrenar la referencia (25 min)

```bash
python workshop/student.py train --task autoencoder --role baseline
squeue -u "$USER"
```

La arquitectura inicial es 10→16→8→2→8→16→10. Entradas: MET_pt, M3l, Z_deltaR, Z_mass, Lep_pt_sum, Z_pt, Lep1Z_pt, Lep2Z_pt, Lep3W_pt y W_mt. Son variables del canal seleccionado; Dataset_ID sirve para separar muestras y nunca es una entrada de la red.

Se minimiza MSE con Adam. El escalado se aprende únicamente del entrenamiento SM, balanceando procesos. El umbral es el percentil 99 de validación SM con igual peso por proceso. Consultar el YAML guardado para los parámetros exactos.

### 3. Diagnóstico (15 min)

Abrir `loss_autoencoder_groupN_baseline.pdf` y `scores_by_process_autoencoder_groupN_baseline.pdf`, donde N es tu grupo; revisar los archivos de métricas y el registro Slurm. Comparar pérdidas de entrenamiento y validación. ¿Las dos siguen bajando? ¿El error significa automáticamente nueva física? ¿Puede reflejar ausencia de representatividad del fondo?

El ejecutor actual también produce ROC y eficiencia W′ al finalizar. **No usar esas cifras para escoger arquitectura o variables.** Guardarlas para la discusión final; si se inspeccionan repetidamente, tratar todo el estudio como exploratorio. El taller no dispone de una nueva muestra W′ independiente para confirmar elecciones.

## Jueves: variar, comparar y explicar

La actividad principal usa los [cuatro grupos YAML y la tabla común](experiments.md). Cada equipo ejecuta referencia y variación asignada; el escenario 4 estudia la dimensión latente. Los cambios sugeridos a continuación son extensiones.

Abrir el YAML de variación del autoencoder indicado por:

```bash
python workshop/student.py files
```

Editar solo el campo asignado dentro de `model`. Guardar y ejecutar el mismo comando para todos los grupos:

```bash
python workshop/student.py train --task autoencoder --role variation
```

No modificar datos, selección, variables, semilla ni umbral. Comparar curvas de pérdida, mejor pérdida de validación y coste de entrenamiento. La referencia W′ se discute al final como evaluación exploratoria; no usarla para elegir el parámetro.

## Limitaciones que deben aparecer en la entrega

- DYJets tiene poca estadística en el piloto anterior (49/17/17); el preflight confirma los conteos efectivos del conjunto compartido. No asumir que las cifras históricas se repiten tras cambiar los archivos.
- Pesos iguales por proceso no representan tasas por luminosidad; no son una predicción de fondo físico.
- Una sola masa/canal W′ no demuestra sensibilidad universal a nueva física.
- Una fluctuación o un evento mal reconstruido no constituye descubrimiento.

**Entrega:** configuración de referencia y variación, dos curvas de pérdida, tabla de métricas SM y una conclusión de tres frases. Agradecer el uso del clúster de alto rendimiento ACARUS de la UNISON.
