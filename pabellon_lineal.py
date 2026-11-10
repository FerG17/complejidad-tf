"""
Constructor generico de pabellones (corredor poligonal + salas a los lados con puertas), pisos 1..n.
Usado por B, C, D, E, F, G, H y J (A e I tienen modulos propios mas detallados).

spec = dict(pisos, corredor=[(x,y)...] en pixeles del plano, cerrado=False, prof=px de profundidad de salas,
            entradas=[(id_exterior, t)], ascensor=(t, id_exterior|None, offset_px)|None,
            escaleras=[(t, offset_px)], salas={piso: {"+": [nombres], "-": [nombres]}})
t = fraccion a lo largo del corredor (0..1). "+" = lado izquierdo del sentido de avance (normal (-dy,dx)); "-" = el otro lado.
En corredores cerrados (anillos) las salas van hacia afuera ("+").
Las salas de nombre "(aprox)" no vienen en las placas con ese numero exacto.
"""
import math

import puertas

ABIERTAS = ("Hall", "Terraza", "Ingreso", "Jardin", "Planta libre", "Ambiente")


def _muestrear(pts, cerrado, espaciado, escala):
    path = list(pts) + ([pts[0]] if cerrado else [])
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])]
    total = sum(seg)
    n = max(int(math.ceil(total * escala / espaciado)), 4)
    ns = n if cerrado else n + 1
    out = []
    for k in range(ns):
        d = total * k / (ns - 1 if not cerrado else n)
        acc = 0.0
        for (a, b), L in zip(zip(path, path[1:]), seg):
            if d <= acc + L + 1e-9:
                f = (d - acc) / L if L else 0
                x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
                dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
                out.append((x, y, -dy, dx))
                break
            acc += L
    return out


def construir(G, sp, alto_piso, base_z, espaciado, escala, costo_esc, costo_asc, pab):
    pts = _muestrear(sp["corredor"], sp.get("cerrado", False), espaciado, escala)
    n = len(pts)
    cerrado = sp.get("cerrado", False)
    prof = sp.get("prof", 28)
    cx = sum(p[0] for p in sp["corredor"]) / len(sp["corredor"])
    cy = sum(p[1] for p in sp["corredor"]) / len(sp["corredor"])

    def normal(k, signo):
        x, y, nx, ny = pts[k]
        if cerrado:   # siempre hacia afuera del centroide
            if (x - cx) * nx + (y - cy) * ny < 0:
                nx, ny = -nx, -ny
            return nx, ny
        return nx * signo, ny * signo

    def k_de(t):
        return min(n - 1, max(0, int(round(t * (n - 1))))) if not cerrado else int(round(t * n)) % n

    anc, ids_por_piso = {}, {}
    for p in range(1, sp["pisos"] + 1):
        z = base_z + (p - 1) * alto_piso
        pre = f"{pab}{p}_"
        ids = []
        for k, (x, y, _, _) in enumerate(pts):
            i = f"{pre}c{k:02d}"
            G.nodo(i, x, y, z, p, pab, "pasillo")
            ids.append(i)
        for a, b in zip(ids, ids[1:]):
            G.arista(a, b, "pasillo")
        if cerrado:
            G.arista(ids[-1], ids[0], "pasillo")
        ids_por_piso[p] = ids
        for s, (t, off) in enumerate(sp["escaleras"]):
            k = k_de(t)
            nx, ny = normal(k, 1 if off >= 0 else -1)
            i = f"{pre}esc{s + 1}"
            G.nodo(i, pts[k][0] + nx * abs(off), pts[k][1] + ny * abs(off), z, p, pab, "escalera", f"Escalera {s + 1}")
            G.arista(ids[k], i, "pasillo")
            anc[(p, f"esc{s + 1}")] = i
        if sp.get("ascensor"):
            t, _, off = sp["ascensor"]
            k = k_de(t)
            nx, ny = normal(k, 1 if off >= 0 else -1)
            i = f"{pre}asc"
            G.nodo(i, pts[k][0] + nx * abs(off), pts[k][1] + ny * abs(off), z, p, pab, "ascensor", f"Ascensor {pab}")
            G.arista(ids[k], i, "pasillo")
            anc[(p, "asc")] = i
        # salas
        for lado, signo in (("+", 1), ("-", -1)):
            nombres = sp["salas"].get(p, {}).get(lado, [])
            for j, etq in enumerate(nombres):
                t = 0.06 + 0.88 * (j + 0.5) / len(nombres)
                k = k_de(t)
                nx, ny = normal(k, signo)
                zx, zy = pts[k][0] + nx * prof, pts[k][1] + ny * prof
                puertas.poner_sala(G, ids[k], f"{pre}r{'p' if signo > 0 else 'n'}{j:02d}", etq, (zx, zy), z, p, pab,
                                   puerta=not etq.startswith(ABIERTAS))
    for p in range(1, sp["pisos"]):
        for s in range(len(sp["escaleras"])):
            G.arista(anc[(p, f"esc{s + 1}")], anc[(p + 1, f"esc{s + 1}")], "escalera", acc=False, w=alto_piso * costo_esc)
        if sp.get("ascensor"):
            G.arista(anc[(p, "asc")], anc[(p + 1, "asc")], "ascensor", acc=True, w=alto_piso + costo_asc)
    # entradas desde el exterior (piso 1) con nodo puerta
    for ext, t in sp["entradas"]:
        k = k_de(t)
        a, b = G.nodos[ext], G.nodos[ids_por_piso[1][k]]
        pid = f"{pab}1_puerta_{ext}"
        G.nodo(pid, (a["x_px"] + b["x_px"]) / 2, (a["y_px"] + b["y_px"]) / 2, base_z, 1, pab, "puerta",
               f"Puerta de ingreso {pab} ({G.nodos[ext]['etiqueta'] or ext})", ancho_m=puertas.ANCHO_DEF, escalon=False)
        G.arista(ext, pid, "puerta")
        G.arista(pid, ids_por_piso[1][k], "puerta")
    if sp.get("ascensor") and sp["ascensor"][1]:
        G.arista(sp["ascensor"][1], anc[(1, "asc")], "puerta")
    return ids_por_piso
