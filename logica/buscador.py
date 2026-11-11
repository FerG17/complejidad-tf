"""
Buscador de nodos por nombre (sin tildes, mayusculas ni orden de palabras).
Entiende sinonimos (salon, bano, laboratorio...), codigos de aula (51 = piso 5, aula 1) y filtros de piso y pabellon:
"salon 51", "e 51", "quinto piso aula 1", "bano piso 3", "labs computo c", "cub 54".
Solo busca puntos identificables: salas, ascensores, escaleras y entradas exteriores.
"""
import re
import unicodedata

TIPOS = {"zona", "ascensor", "escalera", "entrada_accesible", "entrada_campus", "rampa", "salida_emergencia"}
ORDEN_TIPO = {"zona": 0, "ascensor": 1, "escalera": 2}
GENERICAS = {"salon", "salones", "sala", "salas", "aula", "aulas", "ambiente", "ambientes", "clase", "clases"}
PALABRAS_PISO = {"piso", "pisos", "nivel", "planta"}
ORDINALES = {"primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3, "cuarto": 4, "quinto": 5,
             "sexto": 6, "septimo": 7}
SUFIJOS_ORD = {"er", "ro", "do", "to", "mo", "vo", "ra", "da"}
SINONIMOS = {
    "laboratorio": ("lab",), "laboratorios": ("lab",), "lab": ("lab", "laboratorio"), "labs": ("lab",),
    "bano": ("sshh",), "banos": ("sshh",), "wc": ("sshh",), "sh": ("sshh",), "servicios": ("sshh", "servicios"),
    "higienicos": ("sshh",), "higienico": ("sshh",), "toilet": ("sshh",),
    "elevador": ("ascensor",), "elevadores": ("ascensor",), "ascensores": ("ascensor",),
    "gradas": ("escalera",), "escaleras": ("escalera",),
    "discapacitado": ("discap", "discapacitados"), "discapacitados": ("discap", "discapacitados"),
    "discapacidad": ("discap",),
    "computacion": ("computo",), "computadoras": ("computo",), "pc": ("computo",),
    "cubiculo": ("cub",), "cubiculos": ("cub",),
    "oficinas": ("oficina",), "oficina": ("oficina", "of"),
    "restaurante": ("restaurant",), "restaurant": ("restaurant", "kata"), "comedor": ("kata", "restaurant"),
}


def _toks(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z]+|\d+", s)


def _es_piso(s):
    return len(s) == 1 and s.isdigit() and "1" <= s <= "7"


def _extraer(q):
    """Separa del texto el filtro de piso / pabellon. -> (tokens restantes, piso, pabellon)"""
    piso = pab = None
    out = []
    i = 0
    while i < len(q):
        t = q[i]
        sig = q[i + 1] if i + 1 < len(q) else ""
        if t in PALABRAS_PISO and _es_piso(sig):
            piso, i = int(sig), i + 2
        elif t == "p" and _es_piso(sig) and not (i + 2 < len(q) and q[i + 2].isdigit()):
            piso, i = int(sig), i + 2
        elif t in ORDINALES:
            piso, i = ORDINALES[t], i + 1
            if i < len(q) and q[i] in PALABRAS_PISO:
                i += 1
        elif t in PALABRAS_PISO:
            if len(out) >= 2 and out[-1] in SUFIJOS_ORD and _es_piso(out[-2]):
                piso = int(out[-2])
                del out[-2:]
            elif out and _es_piso(out[-1]):
                piso = int(out.pop())
            i += 1
        elif t in ("pabellon", "pab") and len(sig) == 1 and sig.isalpha():
            pab, i = sig.upper(), i + 2
        elif t in ("biblioteca", "biblio"):
            pab, i = "I", i + 1
        else:
            out.append(t)
            i += 1
    return out, piso, pab


def _alternativas(x):
    alt = {x}
    alt.update(SINONIMOS.get(x, ()))
    if len(x) > 3 and x.endswith("s") and x != "sshh":
        alt.add(x[:-1])
    return alt


def _indice(G):
    idx = getattr(G, "_indice_busqueda", None)
    if idx is not None and idx[0] == len(G.nodos):
        return idx[1]
    filas = []
    for n in G.nodos.values():
        if n["tipo"] not in TIPOS:
            continue
        texto = n["nombre"] if n["pab"] else n["nombre"] + " " + n["id"]
        filas.append((n, _toks(texto)))
    G._indice_busqueda = (len(G.nodos), filas)
    return filas


def _coherente(q, t, piso):
    """True si algun numero buscado es el codigo de un aula de ese piso (51 -> piso 5)."""
    p = str(piso)
    return any(x.isdigit() and any(w.isdigit() and len(w) >= 2 and w[0] == p and w.startswith(x) for w in t) for x in q)


def buscar(G, texto, n=8, pab=None, piso=None, tipos=None):
    q, piso_t, pab_t = _extraer(_toks(texto))
    piso = piso if piso is not None else piso_t
    pab = pab if pab is not None else pab_t
    exigidas = [x for x in q if x not in GENERICAS]
    genericas = [x for x in q if x in GENERICAS]
    if piso is not None and genericas:
        exigidas = [f"{piso}{x}" if len(x) == 1 and x.isdigit() else x for x in exigidas]
    if not q and piso is None and pab is None:
        return []
    tipos = tipos or ({"zona"} if genericas and not exigidas else TIPOS)
    res = []
    for nodo, t in _indice(G):
        if nodo["tipo"] not in tipos:
            continue
        if pab is not None and nodo["pab"] != pab:
            continue
        if piso is not None and nodo["piso"] != piso:
            continue
        if not all(any(w.startswith(a) for w in t for a in _alternativas(x)) for x in exigidas):
            continue
        exactas = sum(1 for x in exigidas if x in t)
        coh = 1 if exigidas and nodo["piso"] and _coherente(exigidas, t, nodo["piso"]) else 0
        gen = sum(1 for x in genericas if x in t)
        res.append((-exactas, -coh, -gen, ORDEN_TIPO.get(nodo["tipo"], 3), nodo["piso"], len(nodo["nombre"]),
                    nodo["nombre"], nodo["id"]))
    res.sort()
    return [r[-1] for r in res[:n]]


def opciones_destino(G):
    """Puntos que se pueden elegir como origen/destino: {etiqueta: id}."""
    op = {}
    for i in ("E_SUR", "E_PRIM"):
        op[G.nodos[i]["etiqueta"]] = i
    for n in G.nodos.values():
        if not n["pab"] and n["tipo"] == "zona":
            op[n["etiqueta"]] = n["id"]
    op["Topico (22)"] = "A22"
    op["Rotonda central (11)"] = "RG0"
    for n in G.nodos.values():
        if n["pab"] and n["tipo"] == "zona":
            nom = "Biblioteca" if n["pab"] == "I" else f"Pabellon {n['pab']}"
            op[f"{nom} p{n['piso']} - {n['etiqueta']}"] = n["id"]
    for p in sorted({n["pab"] for n in G.nodos.values() if n["pab"]}):
        for piso in sorted({n["piso"] for n in G.nodos.values() if n["pab"] == p}):
            if p == "I":
                op[f"Pabellon {p} - piso {piso}"] = f"{p}{piso}_hall"
            elif p == "A":
                op[f"Pabellon {p} - piso {piso}"] = f"{p}{piso}_e00"
            else:
                c = [n["id"] for n in G.piso_nodos(p, piso) if n["tipo"] == "pasillo"]
                op[f"Pabellon {p} - piso {piso}"] = c[len(c) // 2]
    return op


if __name__ == "__main__":
    import sys
    from modelo import construccion
    G = construccion.construir()
    for i in buscar(G, " ".join(sys.argv[1:]), n=30):
        print(i, "|", G.nodos[i]["nombre"])
