# 2. Datos NanoAOD

Coloca los ROOT autorizados para el curso en dos carpetas, o usa una ruta compartida de solo lectura indicada por el instructor:

```text
$HOME/Open-Data/Data/
  fondo/*.root
  senal/*.root
```

No subas los ROOT a Git. Para la primera prueba basta un archivo por clase; el generador de configuraciones toma uno por defecto y puede tomar todos con `--max-files 0`.

Comprueba que son arboles NanoAOD y tienen las ramas que usa `filterNanoAOD.py`:

```bash
python - <<'PY'
from pathlib import Path
import uproot

base = Path.home() / "Open-Data/Data"
required = {"Electron_pt", "Electron_eta", "Electron_phi", "Electron_cutBased",
            "Muon_pt", "Muon_eta", "Muon_phi", "Muon_ip3d", "Muon_highPtId",
            "MET_pt", "MET_phi", "HLT_Mu50", "HLT_Ele32_WPTight_Gsf"}
for name in ("fondo", "senal"):
    files = sorted((base / name).glob("*.root"))
    assert files, f"Sin ROOT en {base / name}"
    with uproot.open(files[0]) as source:
        tree = source["Events"]
        print(name, files[0].name, "eventos:", tree.num_entries)
        print("  faltantes:", sorted(required - set(tree.keys())))
        print("  genWeight:", "genWeight" in tree)
PY
```

Esperamos `faltantes: []`. En el ejemplo se usan archivos simulados con `genWeight`; el procesador decide por esa rama si debe aplicar un JSON de luminosidades a datos reales. La seleccion de eventos se registra principalmente con banderas como `3Lep_pass`, `Z_pass` y `W_pass`; no asumas que el numero de filas se reducira.

Si el instructor ofrece datos en una ruta compartida, usa esa ruta en `--data-root` en el paso siguiente. Debe contener las subcarpetas `fondo/` y `senal/`. No inventes ni copies archivos de otras cuentas sin permiso.

Continua en [Procesamiento](03_procesamiento.md).
