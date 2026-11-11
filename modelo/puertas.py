"""
Puertas como NODOS: pasillo -> [nodo puerta] -> sala.
Cada puerta guarda ancho_m y escalon; es accesible si ancho >= ANCHO_MIN y no hay escalon.
Los datos reales de puertas NO estan en los planos: por defecto 0.90 m y sin escalon.
Para marcar una puerta no accesible, agregar en OVERRIDES: {"id_de_la_sala": {"ancho": 0.7}} o {"escalon": True}.
"""
import math

ANCHO_DEF = 0.90
ANCHO_MIN = 0.80
OVERRIDES = {}


def poner_sala(G, ancla, sid, etiqueta, zona_xy, z, piso, pab, puerta=True, puerta_xy=None, tipo_zona="zona"):
    """Crea la sala (nodo zona) y, si puerta=True, el nodo puerta entre `ancla` y la sala."""
    G.nodo(sid, zona_xy[0], zona_xy[1], z, piso, pab, tipo_zona, etiqueta)
    if not puerta:
        G.arista(ancla, sid, "pasillo")
        return sid
    A = G.nodos[ancla]
    if puerta_xy is None:
        puerta_xy = ((A["x_px"] + zona_xy[0]) / 2, (A["y_px"] + zona_xy[1]) / 2)
    pid = sid + "_p"
    ov = OVERRIDES.get(sid, {})
    ancho = ov.get("ancho", ANCHO_DEF)
    esc = ov.get("escalon", False)
    acc = ancho >= ANCHO_MIN and not esc
    G.nodo(pid, puerta_xy[0], puerta_xy[1], z, piso, pab, "puerta", f"Puerta {etiqueta}",
           ancho_m=ancho, escalon=esc)
    G.arista(ancla, pid, "puerta", acc=acc, nota="" if acc else "puerta NO accesible (ancho/escalon)")
    G.arista(pid, sid, "puerta", acc=acc)
    return sid
