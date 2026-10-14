# Práctica 1: Higgs frente a fondo

## Miércoles, primera hora: construir una referencia

**Física:** Higgs de 125 GeV → dos taus; uno produce un electrón o muón y el otro un tau hadrónico. Los neutrinos motivan observables de momento faltante. Los fondos pueden dar una firma similar. El [dataset ATLAS de CERN Open Data](https://opendata.cern.ch/record/328) contiene observables preparados y etiquetas `s`/`b`.

### 1. Inspeccionar datos (10 min)

Desde la raíz del repositorio, sustituir la ruta indicada por el instructor:

```bash
export HIGGS_DATA=/RUTA/COMPARTIDA/atlas-higgs-challenge-2014-v2.csv.gz
python - <<'PY'
import os, pandas as pd
d = pd.read_csv(os.environ['HIGGS_DATA'], nrows=5)
print(d.to_string(index=False))
print(d.columns.tolist())
PY
cp workshop/configs/higgs_baseline.yaml "$HOME/hep-workshop/configs/higgs_baseline.yaml"
```

Editar `data.input` en la copia YAML con la ruta completa del CSV. La referencia selecciona aleatoriamente 50 000 eventos, de forma estratificada y reproducible, con diez observables y semilla 16. `-999` significa información ausente: se reemplaza por la mediana aprendida en entrenamiento y se añaden indicadores de ausencia. Consultar las definiciones de cada variable en el registro oficial.

**Pregunta:** ¿por qué algunos observables de jets están ausentes? ¿Es legítimo usar la ausencia como información?

### 2. Primer entrenamiento (25 min)

```bash
sbatch --account=CUENTA_DEL_CURSO \
  --output="$HOME/hep-workshop/logs/%j.out" \
  workshop/run_cpu.slurm higgs \
  "$HOME/hep-workshop/configs/higgs_baseline.yaml" \
  "$HOME/hep-workshop/results/higgs_baseline"
squeue -u "$USER"
```

No entrenar en el nodo de login. El script pide 2 CPU y 6 GB durante 30 minutos. Si la política local exige otra partición o recursos, el instructor ajusta el archivo antes de clase.

### 3. Interpretar (15 min)

```bash
cat "$HOME/hep-workshop/results/higgs_baseline/metrics.json"
```

Abrir `classification.pdf` o PNG desde Open OnDemand. La ROC muestra eficiencia Higgs frente a aceptación de fondo. El umbral se obtiene de validación buscando 10% de aceptación de fondo. Por defecto **solo se calculan y guardan puntuaciones de validación**.

Se guardan `config.yaml`, `model.joblib`, `splits.csv`, `scores.csv` y `metrics.json`. Las particiones 60/20/20 no se solapan; imputación y escalado se ajustan únicamente con entrenamiento. `EventId`, `Weight`, `Label`, `KaggleSet` y `KaggleWeight` están prohibidos como entradas.

**Preguntas:** ¿basta la exactitud para una muestra desbalanceada? ¿Qué cambia si pedimos menos aceptación de fondo? ¿Una puntuación alta demuestra la presencia de Higgs en datos reales?

## Miércoles, segunda hora: una mejora y evaluación final

Copiar la configuración; mantener dataset, `max_events` y semilla iguales para una comparación justa. Usar una carpeta nueva por ensayo.

```bash
cp "$HOME/hep-workshop/configs/higgs_baseline.yaml" "$HOME/hep-workshop/configs/higgs_candidate.yaml"
```

Elegir **una** modificación:

| Ejercicio | Cambio en YAML | Pregunta |
| --- | --- | --- |
| Árboles potenciados | `model.type: boosted`; opcional `boosted_learning_rate: 0.1` | ¿Aprenden relaciones que la regresión logística no captura? |
| Red neuronal | `model.type: mlp`, `hidden_dims: [32, 16]` | ¿Más capacidad siempre mejora? |
| Variables | Retirar `DER_mass_MMC` de `data.features` | ¿Cuánto depende el clasificador de la masa estimada? |
| Umbral | `background_acceptance: 0.05` | ¿Cómo cambia la eficiencia al reducir fondo? |

Repetir el envío con `higgs_candidate.yaml` y salida `results/higgs_candidate`. Comparar **validación**, no test. El MLP tiene parada temprana con una fracción interna de entrenamiento; no usa nuestro test. Revisar avisos de falta de convergencia y no ocultarlos.

Después de escoger y congelar una configuración, hacer **una evaluación final**:

```bash
sbatch --account=CUENTA_DEL_CURSO \
  --output="$HOME/hep-workshop/logs/%j.out" \
  workshop/run_cpu.slurm higgs-final \
  "$HOME/hep-workshop/configs/higgs_candidate.yaml" \
  "$HOME/hep-workshop/results/higgs_final"
```

Este paso reentrena con la misma configuración/semilla/partición, mantiene el umbral de validación y evalúa test. No hacer nuevas elecciones a partir de ese resultado. El mecanismo es pedagógico, no una barrera de acceso: requiere disciplina del alumno.

## Qué podemos afirmar

Las métricas son **sin pesos físicos**: miden separación en la muestra seleccionada. La precisión/AP depende de la proporción señal/fondo; no es pureza física ni significancia de descubrimiento. `Weight` se conserva en el archivo original, pero no se usa como entrada ni para entrenar. Extensión avanzada: evaluar con pesos y explicar su normalización antes de interpretar rendimientos o AMS. No se estima significancia en esta práctica básica.

**Entrega:** dos configuraciones, tabla con AUC de validación, una evaluación final y tres frases: qué cambiaste, qué observaste y qué limitación tiene tu conclusión.
