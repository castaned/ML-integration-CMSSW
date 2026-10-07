# 6. Problemas frecuentes

| Sintoma | Comprobacion o solucion |
| --- | --- |
| `conda activate` pide `conda init` | `source /apps/miniconda3/etc/profile.d/conda.sh` en cada sesion y nodo de trabajo. |
| `ModuleNotFoundError: ROOT` | Carga `module load root/6.24.08` y exporta `PYTHONPATH="$(root-config --libdir):${PYTHONPATH:-}"`. |
| Slurm rechaza por QOS/cuenta | Revisa que el YAML generado tenga `slurm_params.account: p002` o la cuenta autorizada para tu usuario. No repitas el envio sin comprobar la cola. |
| `CONDA_ENV_NAME no esta definido` | No envies a mano `processing.slurm` o `converting.slurm` sin las variables que prepara el programa. Usa los ejecutores del paso 3. |
| `Permission denied` al crear resultados | Revisa `output_path` en el YAML personal. Debe apuntar a tu `$HOME/Open-Data/Processed/`, no a otra cuenta. |
| `Events` o rama ausente | Verifica un ROOT de entrada con `uproot.open(path).keys()` y el chequeo del paso 2. |
| Slurm dice `COMPLETED` pero faltan artefactos | Lee `logs/job_ID.err`, `logs/job_ID.out` y `stderr.log` de la carpeta de resultados. |
| ONNX menciona `onnxscript` | Instala `onnxscript` en `ml-open-data` y comprueba `python -m pip check`. La rama actual exporta en opset 18. |
| ONNX Runtime muestra advertencias `pthread_setaffinity_np` | Comprueba si la inferencia termina; en pruebas interactivas limita los hilos con `SessionOptions.intra_op_num_threads = 1`. |

Para reportar un problema, incluye la rama y commit (`git status -sb`, `git log -1 --oneline`), el ID del trabajo, el final de sus archivos `.out`/`.err`, y el YAML **sin credenciales ni datos privados**. No publiques archivos ROOT ni tokens en una incidencia de GitHub.

[Volver al inicio del curso](index.md).
