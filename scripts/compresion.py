from __future__ import annotations

import os
import re
import struct
import sys
from collections import Counter
from dataclasses import dataclass

import uproot


def resumen_ramas(ruta: str, etiqueta: str, tree_name: str = "Events") -> dict:
    f = uproot.open(ruta)
    tree = f[tree_name]
    print(f"--- {etiqueta}: {ruta} ---")
    print(f"  Compresion del archivo: {f.file.compression}")

    total_comp = total_uncomp = 0
    filas = {}
    for nombre, rama in tree.items():
        try:
            c, u = rama.compressed_bytes, rama.uncompressed_bytes
        except AttributeError:
            continue
        total_comp += c
        total_uncomp += u
        filas[nombre] = (c, u, str(rama.interpretation))

    print(f"  '{tree_name}': {tree.num_entries} eventos, {len(filas)} ramas medidas")
    print(
        f"  Total comprimido: {total_comp/1e6:.3f} MB   Sin comprimir: {total_uncomp/1e6:.3f} MB"
    )
    print("  Ramas mas pesadas (comprimidas):")
    for nombre, (c, u, interp) in sorted(filas.items(), key=lambda kv: -kv[1][0])[:8]:
        print(
            f"    {nombre:25s} {interp:20s} comprimido={c/1e3:8.1f} kB  sin_comprimir={u/1e3:8.1f} kB"
        )
    print()

    return {
        "total_comp": total_comp,
        "total_uncomp": total_uncomp,
        "ramas": filas,
        "entries": tree.num_entries,
    }


def comparar_ramas(res_a: dict, res_b: dict, etiqueta_a: str, etiqueta_b: str) -> None:
    ramas_a, ramas_b = res_a["ramas"], res_b["ramas"]
    comunes = sorted(set(ramas_a) & set(ramas_b))
    solo_a = sorted(set(ramas_a) - set(ramas_b))
    solo_b = sorted(set(ramas_b) - set(ramas_a))

    print(f"--- Comparacion de ramas ({etiqueta_a} vs {etiqueta_b}) ---")
    if solo_a:
        print(f"  Solo en {etiqueta_a}: {solo_a}")
    if solo_b:
        print(f"  Solo en {etiqueta_b}: {solo_b}")

    diffs = []
    for nombre in comunes:
        ca, _, _ = ramas_a[nombre]
        cb, _, _ = ramas_b[nombre]
        ratio = ca / cb if cb else float("inf")
        diffs.append((ratio, nombre, ca, cb))

    identicas = sum(1 for ratio, *_ in diffs if abs(ratio - 1) < 1e-9)
    print(f"  Ramas comunes: {len(comunes)}   Identicas en tamano: {identicas}")

    diffs.sort(key=lambda d: -abs(d[0] - 1))
    distintas = [d for d in diffs if abs(d[0] - 1) > 1e-9]
    if distintas:
        print("  Ramas con tamano distinto (comprimido):")
        for ratio, nombre, ca, cb in distintas[:15]:
            print(
                f"    {nombre:25s} {etiqueta_a}={ca/1e3:8.1f} kB  {etiqueta_b}={cb/1e3:8.1f} kB  ratio={ratio:6.2f}x"
            )
    else:
        print(
            f"  Todas las ramas comunes pesan EXACTAMENTE igual en {etiqueta_a} y {etiqueta_b}."
        )
    print()


@dataclass
class Layout:
    disk_size: int
    fend: int
    intervals: list
    gaps: list
    total_gap: int


def _iter_all_trees(f) -> list[str]:
    """Nombres (sin ciclo) de todos los TTree de primer nivel del archivo."""
    nombres = []
    for key in f.keys(recursive=False, cycle=False):
        try:
            obj = f[key]
        except Exception:
            continue
        if getattr(obj, "classname", "") == "TTree" or hasattr(obj, "num_entries"):
            nombres.append(key)
    return nombres


def construir_layout(path: str) -> Layout:
    f = uproot.open(path)
    tf = f.file
    d = tf.root_directory

    intervals = [(0, tf.fBEGIN, "header")]

    for name in d.iterkeys():
        k = d.key(name)
        intervals.append((k.fSeekKey, k.fSeekKey + k.fNbytes, f"topkey:{name}"))

    if tf.fSeekInfo:
        intervals.append((tf.fSeekInfo, tf.fSeekInfo + tf.fNbytesInfo, "streamerinfo"))

    intervals.append((d.fSeekKeys, d.fSeekKeys + d.fNbytesKeys, "dirkeys"))
    intervals.append((tf.fSeekFree, tf.fSeekFree + tf.fNbytesFree, "freelist"))

    for treename in _iter_all_trees(f):
        tree = f[treename]
        for bname, branch in tree.items():
            try:
                n = branch.num_baskets
            except Exception:
                continue
            for i in range(n):
                try:
                    key = branch.basket_key(i)
                except Exception:
                    continue
                intervals.append(
                    (
                        key.fSeekKey,
                        key.fSeekKey + key.fNbytes,
                        f"basket:{treename}.{bname}[{i}]",
                    )
                )

    intervals.sort()
    prev_end = 0
    gaps = []
    total_gap = 0
    for start, end, _label in intervals:
        if start > prev_end:
            gap = start - prev_end
            gaps.append((prev_end, start, gap))
            total_gap += gap
        prev_end = max(prev_end, end)
    if tf.fEND > prev_end:
        gap = tf.fEND - prev_end
        gaps.append((prev_end, tf.fEND, gap))
        total_gap += gap

    return Layout(
        disk_size=os.path.getsize(path),
        fend=tf.fEND,
        intervals=intervals,
        gaps=sorted(gaps, key=lambda g: -g[2]),
        total_gap=total_gap,
    )


_TOKEN_RE = re.compile(rb"[A-Za-z_][A-Za-z0-9_]{3,}")


def buscar_evidencia_en_huecos(
    path: str, gaps: list, max_bytes: int = 5_000_000, top_n: int = 12
) -> Counter:
    """Busca tokens tipo nombre-de-rama (identificadores ASCII) dentro de
    los huecos sin identificar, para dar pistas de que datos quedaron
    huerfanos (p.ej. nombres de branches que ya no estan en el arbol
    activo). Se limita a los primeros `max_bytes` de huecos para no leer
    archivos enteros de golpe si el hueco es enorme.
    """
    contador = Counter()
    leidos = 0
    with open(path, "rb") as fh:
        for start, end, size in gaps:
            if leidos >= max_bytes:
                break
            leer = min(size, max_bytes - leidos)
            fh.seek(start)
            data = fh.read(leer)
            leidos += leer
            for m in _TOKEN_RE.finditer(data):
                contador[m.group().decode("latin1")] += 1

    ruido = {
        "ROOT",
        "TFile",
        "TTree",
        "TBasket",
        "TBranch",
        "TObjString",
        "Double",
        "Float",
        "TStreamerInfo",
    }
    for tok in ruido:
        contador.pop(tok, None)

    branch_like = re.compile(r"^(n[A-Z]\w+|[A-Za-z]+_[A-Za-z0-9_]+)$")
    prioritarios = {tok: n for tok, n in contador.items() if branch_like.match(tok)}
    genericos = {
        tok: n for tok, n in contador.items() if n >= 3 and tok not in prioritarios
    }
    if prioritarios:
        ordenados = sorted(prioritarios.items(), key=lambda kv: (-kv[1], -len(kv[0])))
        return Counter(dict(ordenados[:top_n]))
    ordenados = sorted(genericos.items(), key=lambda kv: (-kv[1], -len(kv[0])))
    return Counter(dict(ordenados[:top_n]))


def resumen_layout(path: str, etiqueta: str) -> Layout:
    layout = construir_layout(path)
    pct = 100 * layout.total_gap / layout.disk_size if layout.disk_size else 0
    print(f"--- Layout de bytes: {etiqueta}: {path} ---")
    print(f"  Tamano en disco: {layout.disk_size/1e6:.3f} MB")
    print(
        f"  Bytes identificados (keys+streamerinfo+baskets): {(layout.disk_size - layout.total_gap)/1e6:.3f} MB"
    )
    print(
        f"  Bytes SIN IDENTIFICAR (huerfanos): {layout.total_gap/1e6:.3f} MB  ({pct:.1f}% del archivo)"
    )

    if layout.total_gap > 0:
        print("  Huecos mas grandes (start, end, tamano):")
        for start, end, size in layout.gaps[:5]:
            print(f"    [{start:>10d} - {end:>10d}]  {size/1e3:10.1f} kB")

        evidencia = buscar_evidencia_en_huecos(path, layout.gaps)
        if evidencia:
            print(
                "  Identificadores encontrados dentro de los huecos (posibles branches huerfanas):"
            )
            for tok, n in evidencia.items():
                print(f"    {tok:30s} x{n}")
    else:
        print("  Archivo limpio: no hay bytes huerfanos.")
    print()
    return layout


def main():
    if len(sys.argv) < 3:
        print(
            f'Uso: python {sys.argv[0]} archivoA.root archivoB.root ["Etiqueta A"] ["Etiqueta B"]'
        )
        sys.exit(1)

    ruta_a, ruta_b = sys.argv[1], sys.argv[2]
    etiqueta_a = sys.argv[3] if len(sys.argv) > 3 else "A"
    etiqueta_b = sys.argv[4] if len(sys.argv) > 4 else "B"

    res_a = resumen_ramas(ruta_a, etiqueta_a)
    res_b = resumen_ramas(ruta_b, etiqueta_b)
    comparar_ramas(res_a, res_b, etiqueta_a, etiqueta_b)

    layout_a = resumen_layout(ruta_a, etiqueta_a)
    layout_b = resumen_layout(ruta_b, etiqueta_b)

    print("=" * 70)
    print("RESUMEN FINAL")
    print(
        f"  {etiqueta_a}: {layout_a.disk_size/1e6:.3f} MB en disco "
        f"({res_a['total_comp']/1e6:.3f} MB de Events, "
        f"{layout_a.total_gap/1e6:.3f} MB huerfanos)"
    )
    print(
        f"  {etiqueta_b}: {layout_b.disk_size/1e6:.3f} MB en disco "
        f"({res_b['total_comp']/1e6:.3f} MB de Events, "
        f"{layout_b.total_gap/1e6:.3f} MB huerfanos)"
    )
    ratio_disco = (
        layout_a.disk_size / layout_b.disk_size if layout_b.disk_size else float("inf")
    )
    ratio_events = (
        res_a["total_comp"] / res_b["total_comp"]
        if res_b["total_comp"]
        else float("inf")
    )
    print(f"  Ratio tamano en disco ({etiqueta_a}/{etiqueta_b}): {ratio_disco:.2f}x")
    print(
        f"  Ratio tamano de 'Events' ({etiqueta_a}/{etiqueta_b}): {ratio_events:.2f}x"
    )
    if abs(ratio_disco - ratio_events) / max(ratio_events, 1e-9) > 0.1:
        print(
            "  -> La diferencia de tamaño en disco NO se explica por el contenido de "
            "'Events': revisa la seccion de huerfanos arriba."
        )


if __name__ == "__main__":
    main()
