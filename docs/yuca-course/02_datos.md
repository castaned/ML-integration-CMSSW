# Datos compartidos: entender NanoAOD

**No debes descargar los datasets.** Los archivos originales del curso estarán disponibles en una carpeta compartida de Yuca. Esa carpeta se utiliza para lectura; las selecciones, tablas y modelos se guardan en tu cuenta.

## 1. Observar los eventos

Las rutas compartidas ya quedaron registradas durante la preparación del entorno. Desde la raíz del repositorio, ejecutar sin cambiar el comando:

```bash
python workshop/student.py inspect
```

El programa abre un NanoAOD de cada proceso y muestra su número de eventos y ejemplos de electrones, muones y momento faltante. No es necesario elegir ni escribir el nombre de un archivo ROOT.

Cada entrada de Events corresponde a un evento; las colecciones Electron y Muon contienen cantidades variables de partículas. Las masas de candidatos no se toman como etiquetas: se construirán a partir de los leptones seleccionados.

Si no aparecen archivos o no puedes abrirlos, detener el procesamiento y solicitar ayuda con la ruta o los permisos. No copiar los datasets a tu HOME para intentar resolver un fallo de acceso.

## 3. Separar entradas compartidas de salidas personales

```text
Carpeta compartida del curso (lectura)
  Higgs125/*.root
  ZZ4L/*.root

Tu cuenta: $HOME/hep-workshop/ (escritura)
  configs/       YAML personales
  extraction/    observables y conteos de selección
  logs/          registros de trabajos
  results/       modelos, métricas y gráficas
```

No subir los ROOT al repositorio ni modificar archivos compartidos. Cada experimento debe tener una carpeta de salida nueva para conservar la referencia.

Continuar con [Análisis de NanoAOD y clasificación Higgs](../practical-ml-hep/higgs.md): seleccionar leptones → reconstruir candidatos → generar gráficas y HDF5 → entrenar y evaluar.
