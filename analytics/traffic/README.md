# Historial de uso del repositorio

Registro de estadísticas agregadas de `castaned/ML-integration-CMSSW`, para documentar el alcance del software y su evolución alrededor de las actividades del curso.

- `daily.csv`: última observación disponible de clones y visitas para cada fecha UTC. Las ventanas solapadas reemplazan los valores del mismo día; no se suman.
- `snapshots/`: capturas originales de la API, con fecha de consulta y totales de su ventana de 14 días.

## Interpretación

El total de clones históricos se puede obtener sumando una vez los conteos diarios disponibles. **No deben sumarse los totales móviles de 14 días.** Los días ausentes no se interpretan como cero y el día actual está incompleto. Pueden existir revisiones recientes de GitHub.

Los usuarios únicos diarios no se pueden sumar para obtener usuarios únicos de todo el historial. Los únicos de cada ventana se conservan únicamente como cifras de esa ventana.

Las cifras corresponden al repositorio completo: pueden incluir bots, automatizaciones, trabajo de desarrollo y personas ajenas al curso. No identifican estudiantes, cuentas o IP, no registran el uso interno del software y no permiten atribuir una clonación a una actividad particular. Las visitas son a GitHub, no a GitHub Pages.

## Conservación

Primera captura: 17 de octubre de 2026. GitHub solo expone los últimos 14 días; el historial anterior que no se hubiera guardado no se puede recuperar con este procedimiento. Una tarea diaria en este chat conserva nuevas capturas y publica únicamente estos archivos agregados en la rama `opendata_dev`. La máquina local y la aplicación deben estar disponibles para esa tarea.

La fecha oficial de la escuela es 19–23 de octubre de 2026. Conviene comparar días previos, durante y después del taller; esa comparación describe una asociación temporal, no una atribución causal. Para evaluar mejoras del software, complementar las cifras con problemas reportados, propuestas y resultados reproducibles de los participantes.

## Ejecución manual

Desde la raíz del repositorio:

```bash
python scripts/collect_github_traffic.py --git-credential
```

El script utiliza la credencial Git ya autorizada sin guardarla en los archivos. También admite `GITHUB_TOKEN` mediante una variable de entorno. No imprimir ni guardar tokens en el repositorio. El permiso requerido para las métricas es Administration: read.

[API oficial de tráfico de GitHub](https://docs.github.com/en/rest/metrics/traffic).
