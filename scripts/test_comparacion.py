"""
Compara, rama por rama, los TTrees de archivos .root que se encuentran en dos
carpetas.Solo se comparan entre si los archivos que "corresponden", es
decir, los que tienen la misma ruta relativa (mismo nombre de archivo, y
misma subcarpeta si aplica) dentro de las dos carpetas. Un archivo que solo
existe en una de las dos carpetas se reporta como "sin pareja" y NUNCA se
compara contra otro archivo distinto.

Imprime un resumen en consola y, opcionalmente, genera una grafica por cada
par de archivos comparado.

Ejemplo de uso:
    python test_comparacion.py carpetaA carpetaB

"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import uproot

EVENT_ID_BRANCHES = ("run", "luminosityBlock", "event")


@dataclass
class BranchComparison:
    name: str
    n_compared: int = 0
    n_diff: int = 0
    examples: list = field(default_factory=list)
    skipped_reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.skipped_reason is None and self.n_diff == 0


def titulo(texto: str) -> None:
    print(f"\n{texto}\n{'-' * len(texto)}")


# --------------------------------------------------------------------------
# Localizar y emparejar archivos entre las dos carpetas
# --------------------------------------------------------------------------
def listar_archivos_root(
    carpeta: Path, patron: str, recursivo: bool
) -> dict[str, Path]:
    """Devuelve {ruta_relativa: ruta_absoluta} de los archivos que coinciden
    con `patron` dentro de `carpeta`."""
    rutas = carpeta.rglob(patron) if recursivo else carpeta.glob(patron)
    archivos = {}
    for ruta in sorted(rutas):
        if ruta.is_file():
            relativa = ruta.relative_to(carpeta).as_posix()
            archivos[relativa] = ruta
    return archivos


def emparejar_carpetas(carpeta_a: Path, carpeta_b: Path, patron: str, recursivo: bool):
    """Empareja los archivos de dos carpetas por su ruta relativa (mismo
    nombre / subcarpeta). Solo los que existen en AMBAS carpetas se
    consideran 'correspondientes' y se devuelven para comparar; el resto se
    reporta como sin pareja y jamas se compara entre si."""
    archivos_a = listar_archivos_root(carpeta_a, patron, recursivo)
    archivos_b = listar_archivos_root(carpeta_b, patron, recursivo)

    claves_a, claves_b = set(archivos_a), set(archivos_b)
    comunes = sorted(claves_a & claves_b)
    solo_a = sorted(claves_a - claves_b)
    solo_b = sorted(claves_b - claves_a)

    titulo("Archivos .root encontrados")
    print(f"  Carpeta A ({carpeta_a}): {len(archivos_a)} archivo(s)")
    print(f"  Carpeta B ({carpeta_b}): {len(archivos_b)} archivo(s)")
    print(f"  Con pareja en ambas carpetas (se compararan): {len(comunes)}")

    if solo_a:
        print(
            f"  SOLO en A, sin pareja en B -> NO se comparan ({len(solo_a)}): {solo_a}"
        )
    if solo_b:
        print(
            f"  SOLO en B, sin pareja en A -> NO se comparan ({len(solo_b)}): {solo_b}"
        )
    if not comunes:
        print("  No hay ningun par de archivos correspondientes para comparar.")

    pares = {clave: (archivos_a[clave], archivos_b[clave]) for clave in comunes}
    return pares, solo_a, solo_b


# --------------------------------------------------------------------------
# Apertura de archivos / calculo de orden de eventos
# --------------------------------------------------------------------------
def abrir_tree(ruta_root: str, nombre_tree: str):
    """Abre un archivo .root y devuelve el TTree pedido (tolera sufijos de
    ciclo tipo 'Events;1')."""
    archivo = uproot.open(ruta_root)
    if nombre_tree in archivo:
        return archivo[nombre_tree]

    candidatos = [k for k in archivo.keys() if k.split(";")[0] == nombre_tree]
    if not candidatos:
        disponibles = list(archivo.keys())
        raise KeyError(
            f"No existe el TTree '{nombre_tree}' en {ruta_root}. Disponibles: {disponibles}"
        )
    return archivo[candidatos[0]]


def calcular_orden_por_evento(tree):
    """Devuelve los indices que ordenan los eventos por (run, luminosityBlock,
    event), para poder comparar dos archivos aunque los eventos esten en
    distinto orden. Si el tree no tiene esas ramas, devuelve None."""
    ramas_disponibles = [b for b in EVENT_ID_BRANCHES if b in tree.keys()]
    if len(ramas_disponibles) < 2:
        return None, ramas_disponibles, None

    ids = tree.arrays(ramas_disponibles, library="np")
    prioridad = [ids[nombre] for nombre in reversed(ramas_disponibles)]
    indices_ordenados = np.lexsort(prioridad)
    return indices_ordenados, ramas_disponibles, ids


def alinear_ids_evento(ids, orden, n):
    """Reordena (si aplica) y recorta a `n` los valores de run/luminosityBlock
    /event, para poder identificar los eventos de ejemplo que se impriman."""
    if ids is None:
        return None
    salida = {}
    for nombre, valores in ids.items():
        v = valores[orden] if orden is not None else valores
        salida[nombre] = v[:n]
    return salida


def es_array_simple(valores) -> bool:
    """True si la rama es un array plano (un numero por evento). False si es
    'jagged' (longitud variable, p.ej. Electron_pt antes de filtrar) -- esas
    no se comparan valor a valor aqui."""
    return isinstance(valores, np.ndarray) and valores.dtype != object


def comparar_una_rama(
    nombre, valores_a, valores_b, rtol, atol, max_ejemplos, ids_alineados=None
) -> BranchComparison:
    resultado = BranchComparison(name=nombre)

    if not (es_array_simple(valores_a) and es_array_simple(valores_b)):
        resultado.skipped_reason = (
            "array irregular (jagged), no comparable directamente"
        )
        return resultado

    n = min(len(valores_a), len(valores_b))
    a, b = valores_a[:n], valores_b[:n]
    resultado.n_compared = n

    es_float = np.issubdtype(a.dtype, np.floating) or np.issubdtype(
        b.dtype, np.floating
    )
    if es_float:
        coinciden = np.isclose(a, b, rtol=rtol, atol=atol, equal_nan=True)
    else:
        coinciden = a == b

    indices_diferentes = np.where(~coinciden)[0]
    resultado.n_diff = len(indices_diferentes)

    def construir_evento(i: int) -> dict:
        i = int(i)
        valor_a, valor_b = a[i].item(), b[i].item()
        evento = {"idx": i}
        if ids_alineados is not None:
            for clave, valores_id in ids_alineados.items():
                if i < len(valores_id):
                    evento[clave] = valores_id[i].item()
        evento["valor_A"] = valor_a
        evento["valor_B"] = valor_b
        if es_float:
            try:
                evento["diferencia_abs"] = valor_b - valor_a
            except TypeError:
                pass
        return evento

    resultado.examples = [
        construir_evento(i) for i in indices_diferentes[:max_ejemplos]
    ]
    return resultado


def comparar_todas_las_ramas(
    tree_a,
    tree_b,
    ramas_comunes,
    orden_a,
    orden_b,
    rtol,
    atol,
    max_ejemplos,
    ids_alineados=None,
):
    resultados = {}
    for nombre in sorted(ramas_comunes):
        valores_a = tree_a[nombre].array(library="np")
        valores_b = tree_b[nombre].array(library="np")

        if orden_a is not None:
            valores_a = valores_a[orden_a]
            valores_b = valores_b[orden_b]

        resultados[nombre] = comparar_una_rama(
            nombre, valores_a, valores_b, rtol, atol, max_ejemplos, ids_alineados
        )
    return resultados


# --------------------------------------------------------------------------
# Reporte por rama y por par de archivos
# --------------------------------------------------------------------------
def registrar_resumen_ramas(branches_a, branches_b):
    comunes = branches_a & branches_b
    solo_a = branches_a - branches_b
    solo_b = branches_b - branches_a

    titulo("Ramas (branches)")
    print(
        f"  En A: {len(branches_a)}   En B: {len(branches_b)}   Comunes: {len(comunes)}"
    )
    if solo_a:
        print(f"  Solo en A: {sorted(solo_a)}")
    if solo_b:
        print(f"  Solo en B: {sorted(solo_b)}")
    return comunes, solo_a, solo_b


def formatear_evento(evento: dict) -> str:
    """Da formato legible a un evento con diferencia: indice, run/lumi/event
    si estan disponibles, y los valores A/B."""
    partes = [f"evento #{evento['idx']}"]
    for clave in ("run", "luminosityBlock", "event"):
        if clave in evento:
            partes.append(f"{clave}={evento[clave]}")
    partes.append(f"A={evento['valor_A']}")
    partes.append(f"B={evento['valor_B']}")
    if "diferencia_abs" in evento:
        partes.append(f"diff={evento['diferencia_abs']:+.6g}")
    return "  ".join(partes)


def registrar_resultados_por_rama(resultados: dict[str, BranchComparison]) -> None:
    titulo("Comparacion valor por valor")
    if not resultados:
        print("  (no hay ramas comunes para comparar valor a valor)")
        return

    ancho_nombre = max(len(n) for n in resultados) + 2
    for nombre, r in resultados.items():
        if r.skipped_reason:
            print(f"  [SKIP] {nombre:<{ancho_nombre}} {r.skipped_reason}")
            continue

        estado = "OK  " if r.ok else "DIFF"
        print(
            f"  [{estado}] {nombre:<{ancho_nombre}} diferencias={r.n_diff}/{r.n_compared}"
        )
        for evento in r.examples:
            print(f"           {formatear_evento(evento)}")


def registrar_veredicto_par(
    resultados, n_eventos_a, n_eventos_b, ramas_solo_a, ramas_solo_b
):
    ramas_con_diferencias = [
        n for n, r in resultados.items() if not r.ok and not r.skipped_reason
    ]
    todo_coincide = (
        not ramas_con_diferencias
        and n_eventos_a == n_eventos_b
        and not ramas_solo_a
        and not ramas_solo_b
    )

    titulo("Veredicto del par")
    print(f"  Eventos -> A: {n_eventos_a}   B: {n_eventos_b}")
    print(f"  Ramas con diferencias: {len(ramas_con_diferencias)}")

    if todo_coincide:
        print("  Este par es EQUIVALENTE.")
    else:
        print("  Este par NO es totalmente equivalente (ver detalle arriba).")

    return todo_coincide


def generar_grafica(resultados, tree_a, tree_b, orden_a, orden_b, ruta_salida):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ramas_graficables = [n for n, r in resultados.items() if not r.skipped_reason]
    if not ramas_graficables:
        print("  (sin ramas graficables; se omite la grafica para este par)")
        return

    n_col = min(4, len(ramas_graficables))
    n_fila_scatter = math.ceil(len(ramas_graficables) / n_col)

    fig = plt.figure(figsize=(4 * n_col, 4 * n_fila_scatter + 4))
    fig.suptitle("Comparacion filtro A vs filtro B", fontsize=14, fontweight="bold")

    for i, nombre in enumerate(ramas_graficables, start=1):
        valores_a = tree_a[nombre].array(library="np")
        valores_b = tree_b[nombre].array(library="np")
        if orden_a is not None:
            valores_a = valores_a[orden_a]
            valores_b = valores_b[orden_b]
        n = min(len(valores_a), len(valores_b))
        valores_a, valores_b = valores_a[:n], valores_b[:n]

        ax = fig.add_subplot(n_fila_scatter + 1, n_col, i)
        ax.scatter(valores_a, valores_b, s=8, alpha=0.5, color="#2563eb")

        lo = min(valores_a.min(), valores_b.min())
        hi = max(valores_a.max(), valores_b.max())
        ax.plot([lo, hi], [lo, hi], "--", color="gray", linewidth=1)

        r = resultados[nombre]
        color_titulo = "#16a34a" if r.ok else "#dc2626"
        ax.set_title(nombre, fontsize=9, color=color_titulo)
        ax.set_xlabel("A", fontsize=8)
        ax.set_ylabel("B", fontsize=8)
        ax.tick_params(labelsize=7)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(ruta_salida, dpi=150)
    print(f"  Grafica guardada en: {ruta_salida}")


def comparar_par(nombre_par: str, ruta_a: Path, ruta_b: Path, args) -> bool:
    """Compara un unico par de archivos que ya se sabe que corresponden entre
    si (misma ruta relativa en las dos carpetas). Devuelve si el par es
    equivalente."""
    titulo(f"PAR: {nombre_par}")
    print(f"  A: {ruta_a}")
    print(f"  B: {ruta_b}")

    try:
        tree_a = abrir_tree(str(ruta_a), args.tree)
        tree_b = abrir_tree(str(ruta_b), args.tree)
    except Exception as exc:
        print(f"  ERROR al abrir el par '{nombre_par}': {exc}")
        return False

    ramas_comunes, ramas_solo_a, ramas_solo_b = registrar_resumen_ramas(
        set(tree_a.keys()), set(tree_b.keys())
    )

    n_eventos_a, n_eventos_b = tree_a.num_entries, tree_b.num_entries
    titulo("Numero de eventos (post-filtro)")
    print(f"  A: {n_eventos_a}   B: {n_eventos_b}")

    orden_a, ramas_id_a, ids_a = calcular_orden_por_evento(tree_a)
    orden_b, ramas_id_b, ids_b = calcular_orden_por_evento(tree_b)

    titulo("Alineacion de eventos")
    if orden_a is not None and ramas_id_a == ramas_id_b:
        print(f"  Alineando por {ramas_id_a} ...")
    else:
        orden_a = orden_b = None
        ids_a = None
        print(
            "  No se pudo alinear por run/luminosityBlock/event; se compara por orden de escritura."
        )

    ramas_a_comparar = ramas_comunes - set(ramas_id_a if orden_a is not None else [])
    ids_alineados = alinear_ids_evento(ids_a, orden_a, min(n_eventos_a, n_eventos_b))

    try:
        resultados = comparar_todas_las_ramas(
            tree_a,
            tree_b,
            ramas_a_comparar,
            orden_a,
            orden_b,
            args.rtol,
            args.atol,
            args.max_report,
            ids_alineados,
        )
    except Exception as exc:
        print(f"  ERROR al comparar ramas del par '{nombre_par}': {exc}")
        return False

    registrar_resultados_por_rama(resultados)
    veredicto_ok = registrar_veredicto_par(
        resultados, n_eventos_a, n_eventos_b, ramas_solo_a, ramas_solo_b
    )

    if not args.no_plot:
        ruta_plot = Path(args.plot_dir) / (nombre_par.replace("/", "__") + ".png")
        ruta_plot.parent.mkdir(parents=True, exist_ok=True)
        try:
            generar_grafica(
                resultados, tree_a, tree_b, orden_a, orden_b, str(ruta_plot)
            )
        except Exception as exc:
            print(f"  No se pudo generar la grafica para '{nombre_par}': {exc}")

    return veredicto_ok


# --------------------------------------------------------------------------
# Resumen global / CLI
# --------------------------------------------------------------------------
def registrar_resumen_global(veredictos: dict, solo_a: list, solo_b: list) -> bool:
    n_total = len(veredictos)
    n_ok = sum(1 for ok in veredictos.values() if ok)
    n_mal = n_total - n_ok

    titulo("RESUMEN GLOBAL")
    print(f"  Pares comparados: {n_total}")
    print(f"  Equivalentes: {n_ok}")
    print(f"  Con diferencias / errores: {n_mal}")
    if solo_a:
        print(f"  Archivos sin pareja en B (no comparados): {len(solo_a)} -> {solo_a}")
    if solo_b:
        print(f"  Archivos sin pareja en A (no comparados): {len(solo_b)} -> {solo_b}")

    if n_total == 0:
        print("  No se comparo ningun par de archivos.")
        todo_ok = False
    else:
        todo_ok = n_mal == 0 and not solo_a and not solo_b

    if todo_ok:
        print("RESULTADO FINAL: todos los archivos correspondientes son EQUIVALENTES.")
    else:
        print(
            "RESULTADO FINAL: hay diferencias, errores o archivos sin comparar (ver detalle arriba)."
        )
    return todo_ok


def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "carpetaA", help="Carpeta con archivos .root filtrados (p.ej. salida CMSSW)"
    )
    ap.add_argument(
        "carpetaB",
        help="Carpeta con archivos .root filtrados (p.ej. salida mini_nanotools)",
    )
    ap.add_argument(
        "--tree", default="Events", help="Nombre del TTree (default: Events)"
    )
    ap.add_argument(
        "--pattern",
        default="*.root",
        help="Patron glob para localizar archivos (default: *.root)",
    )
    ap.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="No buscar dentro de subcarpetas (por default si busca en subcarpetas)",
    )
    ap.add_argument(
        "--rtol", type=float, default=1e-5, help="Tolerancia relativa para floats"
    )
    ap.add_argument(
        "--atol", type=float, default=1e-8, help="Tolerancia absoluta para floats"
    )
    ap.add_argument(
        "--max-report",
        type=int,
        default=10,
        dest="max_report",
        help="Ejemplos de diferencias a mostrar en consola por rama (default: 10)",
    )
    ap.add_argument(
        "--plot-dir",
        default="plots_comparacion",
        dest="plot_dir",
        help="Carpeta donde guardar una grafica por cada par comparado",
    )
    ap.add_argument("--no-plot", action="store_true", help="No generar graficas")
    ap.set_defaults(recursive=True)
    return ap.parse_args()


def main():
    args = parse_args()

    carpeta_a = Path(args.carpetaA)
    carpeta_b = Path(args.carpetaB)

    for carpeta, etiqueta in ((carpeta_a, "A"), (carpeta_b, "B")):
        if not carpeta.is_dir():
            print(f"La carpeta {etiqueta} no existe o no es un directorio: {carpeta}")
            sys.exit(2)

    pares, solo_a, solo_b = emparejar_carpetas(
        carpeta_a, carpeta_b, args.pattern, args.recursive
    )

    veredictos = {}
    for nombre_par, (ruta_a, ruta_b) in pares.items():
        veredictos[nombre_par] = comparar_par(nombre_par, ruta_a, ruta_b, args)

    todo_ok = registrar_resumen_global(veredictos, solo_a, solo_b)
    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
