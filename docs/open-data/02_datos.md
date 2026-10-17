# Archivos de CERN Open Data

## Selección de muestras

Consultar el [portal CERN Open Data](https://opendata.cern.ch/) y la descripción de cada registro. Para este flujo, seleccionar muestras CMS en formato **NanoAOD o NANOAODSIM** y conservar la identificación del dataset, la campaña y la lista de archivos utilizados.

NanoAOD se almacena en archivos ROOT. La tabla `Events` contiene una entrada por evento y colecciones como `Electron`, `Muon` y `Jet`. No todos los productos del portal tienen este formato; una tabla CSV preparada para aprendizaje automático no se procesa con el filtro NanoAOD.

## Organización de los archivos

Descargar o copiar los archivos elegidos a una ubicación accesible desde los nodos de procesamiento. También puede utilizarse un almacenamiento compartido ya disponible. El ejemplo general del generador de YAML espera:

```text
Open-Data/Data/
  fondo/*.root
  senal/*.root
```

Conservar los archivos originales y guardar los productos del análisis en una ruta distinta.

## Comprobación de una entrada

Sustituir la ruta por un archivo real:

```bash
python - <<'CHECK'
import uproot
path = "/ruta/al/archivo.root"
with uproot.open(path) as source:
    events = source["Events"]
    print("Eventos:", events.num_entries)
    print("Ramas:", list(events.keys())[:20])
CHECK
```

Revisar que las ramas requeridas por el filtro estén disponibles. Mantener un mapa consistente entre cada proceso y su `Dataset_ID`; las etiquetas identifican las muestras, no son variables de entrada de las redes.

[Continuar: procesamiento y HDF5](03_procesamiento.md).
