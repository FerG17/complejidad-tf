"""
Ascensores del campus como unidades completas (todos los pisos + su entrada exterior) y retos de ejemplo.
Un ascensor "fuera de servicio" bloquea todos sus nodos: nadie puede entrar, salir ni cruzar por el.
"""
import re

NOTAS = {"J": " (sirve a J y B)"}


def catalogo(G):
    """-> lista de dict(clave, nombre, nodos) ordenada: ascensores de pabellon y luego los exteriores sueltos."""
    grupos = {}
    for n in G.nodos.values():
        m = re.match(r"^([A-Z])\d+_(.+)$", n["id"])
        if n["tipo"] != "ascensor" or not n["pab"] or not m:
            continue
        g = grupos.setdefault(f"{m.group(1)}:{m.group(2)}", dict(nodos=[], nombre=""))
        g["nodos"].append(n["id"])
        if n["piso"] == 1:
            g["nombre"] = (n["etiqueta"] or f"Ascensor {n['pab']}") + NOTAS.get(n["pab"], "")
    for n in G.nodos.values():
        if n["tipo"] != "ascensor" or n["pab"]:
            continue
        for v, _, _, _ in G.adj[n["id"]]:
            dueno = next((g for g in grupos.values() if v in g["nodos"]), None)
            if dueno:
                dueno["nodos"].append(n["id"])
                break
        else:
            grupos[f"EXT:{n['id']}"] = dict(nodos=[n["id"]], nombre=n["nombre"])
    return [dict(clave=k, **v) for k, v in sorted(grupos.items(), key=lambda kv: (kv[0].startswith("EXT"), kv[0]))]


def _alcanzables(G, ini, bloq, solo_acc=True):
    vis = {ini}
    pila = [ini]
    while pila:
        u = pila.pop()
        for v, _, _, acc in G.adj[u]:
            if v in vis or v in bloq or (solo_acc and not acc):
                continue
            vis.add(v)
            pila.append(v)
    return vis


def pisos_sin_acceso(G, bloq, origen="E_SUR"):
    """-> {pabellon: [pisos]} donde ninguna sala es alcanzable por ruta accesible desde `origen`."""
    vis = _alcanzables(G, origen, set(bloq))
    por_piso = {}
    for n in G.nodos.values():
        if n["pab"] and n["tipo"] == "zona":
            por_piso.setdefault((n["pab"], n["piso"]), []).append(n["id"] in vis)
    res = {}
    for (p, piso), ok in sorted(por_piso.items()):
        if not any(ok):
            res.setdefault(p, []).append(piso)
    return res


def texto_pisos(res):
    def rangos(pisos):
        out, i = [], 0
        while i < len(pisos):
            j = i
            while j + 1 < len(pisos) and pisos[j + 1] == pisos[j] + 1:
                j += 1
            out.append(f"{pisos[i]}" if i == j else f"{pisos[i]}-{pisos[j]}")
            i = j + 1
        return ", ".join(out)
    return "; ".join(f"{p} pisos {rangos(v)}" for p, v in sorted(res.items())) or "ninguno"


def _sala(G, pab, piso):
    zs = [n for n in G.nodos.values() if n["pab"] == pab and n["piso"] == piso and n["tipo"] == "zona"]
    return min(zs, key=lambda n: n["id"])["id"]


def retos(G):
    """Escenarios que muestran como cambia la ruta (o desaparece) al sacar ascensores de servicio."""
    entrada = "E_SUR"
    cub54 = next(i for i, n in G.nodos.items() if n["etiqueta"].startswith("CUB-54"))
    return [
        dict(titulo="G sin ascensor: desvio por E y F",
             nota="El ascensor de G (el que tambien sirve a F) esta fuera de servicio: se sube por el ascensor de E y se "
                  "cruza por F. Destino de ejemplo: G piso 3.",
             origen=entrada, destino=_sala(G, "G", 3), fuera=["G:asc"]),
        dict(titulo="E y G sin ascensor: E, F y G aislados",
             nota="Los tres pabellones estan conectados entre si y solo tienen esos dos ascensores. Destino de ejemplo: "
                  "G piso 3.", origen=entrada, destino=_sala(G, "G", 3), fuera=["G:asc", "E:asc"]),
        dict(titulo="J sin ascensor: J y B aislados",
             nota="El ascensor de J sirve tambien a B. Destino de ejemplo: J piso 3.",
             origen=entrada, destino=_sala(G, "J", 3), fuera=["J:asc"]),
        dict(titulo="C se alcanza por D",
             nota="C no tiene ascensor: se sube por el ascensor de D y se cruza a C por la plataforma plana del mismo "
                  "piso. Destino de ejemplo: C piso 3.",
             origen=entrada, destino=_sala(G, "C", 3), fuera=[]),
        dict(titulo="D sin ascensor: D y C aislados",
             nota="C solo se alcanza desde D, y D solo tiene un ascensor. Destino de ejemplo: C piso 3.",
             origen=entrada, destino=_sala(G, "C", 3), fuera=["D:asc"]),
        dict(titulo="Biblioteca: cae un ascensor, sirve el otro",
             nota="Con un ascensor fuera de servicio la ruta cambia de torre. Destino de ejemplo: CUB-54 (piso 7).",
             origen=entrada, destino=cub54, fuera=["I:asc2"]),
        dict(titulo="Biblioteca sin ascensores",
             nota="Con los dos ascensores fuera de servicio no se puede subir. Destino de ejemplo: CUB-54 (piso 7).",
             origen=entrada, destino=cub54, fuera=["I:asc1", "I:asc2"]),
        dict(titulo="Pabellon A: sin ascensor",
             nota="A no tiene ascensor (desmarca 'Solo ruta accesible' para ver la ruta por escaleras). "
                  "Destino de ejemplo: A piso 2.", origen=entrada, destino=_sala(G, "A", 2), fuera=[]),
    ]
