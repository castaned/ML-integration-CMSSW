# Entrega por grupo y comparación colectiva

Los entrenamientos se ejecutan y guardan **en tu cuenta de Yuca**. Después cada grupo sube una selección de resultados a la carpeta compartida del curso, por ejemplo en Google Drive, y completa sus filas en una hoja común. Utilizar el enlace comunicado durante la sesión; aquí no se presupone una carpeta ya creada.

## 1. Preparar la entrega

Terminar referencia y variación del [escenario asignado](experiments.md), revisar los registros y conservar los YAML. Preparar un paquete por práctica, sin datasets ni pesos del modelo.

Preparar la entrega de tu grupo mediante comandos fijos:

```bash
python workshop/student.py package --task higgs
python workshop/student.py package --task autoencoder
```

El programa identifica tu grupo y sus YAML, verifica ambos resultados y guarda paquetes con nombres únicos en tu carpeta personal. No escribir rutas de modelos ni nombres de grupo a mano.

## 2. Subir pocas figuras útiles

Descargar el paquete desde **Files** de Open OnDemand a tu computadora. Abrirlo, completar `conclusiones.md` y subir a la carpeta del grupo el CSV, las configuraciones y las imágenes representativas. También puede conservarse el ZIP como respaldo, pero las figuras y la hoja deben poder verse sin abrirlo.

Organización propuesta en la carpeta compartida del curso:

```text
Grupo_1/
  Higgs/        tabla, YAML, ROC comparativa, conclusiones
  Autoencoder/ tabla, YAML, pérdidas y puntuaciones, conclusiones
Grupo_2/
Grupo_3/
Grupo_4/
```

### Clasificación Higgs

- `ROC_comparison.png`: referencia y variación sobre los mismos eventos de validación y ejes comunes.
- Una `classification.png` por ensayo: ROC y distribución de puntuaciones, dentro de `baseline/` y `variation/`.
- `comparacion.csv`, los dos `config.yaml` y los dos `metrics.json`.

No añadir todas las pruebas realizadas. Entregar la pareja asignada y explicar los avisos de falta de convergencia si aparecieron. Más neuronas o más épocas **pueden** ayudar, pero también aumentar sobreajuste o coste; no constituyen una mejora garantizada.

### Autoencoder CMS

- Curva de pérdida de referencia y de variación: `loss_autoencoder_groupN_baseline.pdf` y `loss_autoencoder_groupN_variation.pdf`.
- Distribución de errores por proceso de ambos ensayos: archivos `scores_by_process_...pdf`.
- `comparacion.csv`, YAML y métricas de ambos ensayos.

No usar la ROC W′ para escoger el parámetro. Si se presenta esa ROC al final, identificarla como **evaluación exploratoria sobre una señal de referencia ya inspeccionada**. No mezclarla con el AUC de validación del clasificador Higgs ni construir un ranking común entre ambas prácticas.

## 3. Completar la hoja compartida

Cada grupo llena únicamente sus filas, conservando las de los demás. Importar los valores del CSV o copiarlos a las dos pestañas de comparación. Las métricas y porcentajes deben indicar conjunto de evaluación y pesos usados.

### Pestaña Higgs: selección del clasificador con validación

[Plantilla Higgs en CSV](../assets/workshop/tabla_higgs.csv)

| Grupo | Ensayo | Parámetro/valor | AUC validación | Eficiencia Higgs | Aceptación fondo | Iteraciones | Tiempo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1–4 | Referencia / variación | | | | | | |

Comparar eficiencia a la misma aceptación nominal de fondo (10%), mismos eventos y semilla. Una diferencia pequeña con poca estadística no demuestra superioridad; no presentar AP como pureza física. Congelar decisiones y realizar después el test final, registrado aparte sin usarlo para nuevas elecciones.

### Pestaña autoencoder: reconstrucción SM y diagnóstico final

[Plantilla autoencoder en CSV](../assets/workshop/tabla_autoencoder.csv)

| Grupo | Ensayo | Parámetro/valor | Pérdida validación SM | Épocas | Tiempo | Aceptación SM test global/por proceso | Observación |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1–4 | Referencia / variación | | | | | | |

La aceptación SM de test es un diagnóstico final: **no usarla para ajustar el modelo**. Reportar conteos por proceso, especialmente si DYJets es escaso. El peso igual por proceso no equivale a tasas por luminosidad.

En autoencoder discutir conjuntamente: curva de entrenamiento/validación, mejor pérdida SM, estabilidad del umbral y comportamiento por proceso. Un espacio latente mayor puede reconstruir mejor tanto SM como W′ y reducir el contraste. No existe aquí una única métrica que pruebe la mejor búsqueda de anomalías.

## 4. Conclusión del grupo y discusión final

Completar en el documento compartido:

1. Antes del entrenamiento esperábamos… porque…
2. Al cambiar únicamente… observamos… respecto a la referencia.
3. La mejora o ausencia de mejora costó… tiempo/iteraciones.
4. La evidencia no permite afirmar…; la siguiente prueba sería…

Presentar cada grupo en dos minutos. Al cierre comparar las cuatro hipótesis con las observaciones: ¿qué cambio parece útil?, ¿es coherente con lo esperado?, ¿qué trade-off aparece?, ¿necesitamos más semillas o estadística?

Un resultado que no mejora aporta valor si la comparación es consistente y la explicación está respaldada por los números y figuras. No atribuir diferencias a un parámetro si además cambiaron datos, cortes o particiones.
