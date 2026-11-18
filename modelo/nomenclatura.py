"""
Nomenclatura de los nodos de sala (etiquetas sin el prefijo "<pabellon> p<piso> - ", que agrega Grafo).

  * Salon X-NN para todo salon o aula; si es laboratorio o taller: Salon/Lab. computo H-41, Salon/Taller de diseno H-43.
  * SSHH hombres / SSHH mujeres / SSHH discapacitados (un solo SSHH si el piso tiene un unico bano).
  * Administracion, Oficina, Almacen y Oficina PTC sin nombre propio llevan un numero correlativo por piso
    (Administracion 1, Administracion 2...): el piso ya distingue las demas plantas.
  * Sin "(aprox)", sin capacidades y sin repetir pabellon o piso dentro de la etiqueta.
"""
import re

GENERICOS = ("Administracion", "Oficina", "Almacen", "Oficina PTC")


def numerar(salas):
    """salas = [(etiqueta, centro, puertas)] de un piso -> mismas salas con los nombres genericos numerados."""
    cuenta = {}
    out = []
    for etq, centro, pts in salas:
        if etq in GENERICOS:
            cuenta[etq] = cuenta.get(etq, 0) + 1
            etq = f"{etq} {cuenta[etq]}"
        out.append((etq, centro, pts))
    return out


REGLAS = (
    (r"\(aprox\)", "sin '(aprox)'"),
    (r"^Aula (?!Magna)", "usar 'Salon' en vez de 'Aula'"),
    (r"\([A-J] p\d", "no repetir pabellon y piso en la etiqueta"),
    (r"\b(damas|varones)\b", "usar 'mujeres' / 'hombres'"),
    (r"^(Lab\.|Taller|Capstone|Ambiente).*\b[A-H]-\d\d$", "salon numerado: prefijo 'Salon/'"),
    (r"\((?:14|20|25|30|40)\)$", "sin capacidad entre parentesis"),
)


def problemas(etiqueta):
    """Reglas de nomenclatura que incumple una etiqueta de sala (lista vacia si esta bien)."""
    out = [msg for patron, msg in REGLAS if re.search(patron, etiqueta)]
    if etiqueta in GENERICOS:
        out.append("nombre generico sin numero")
    return out
