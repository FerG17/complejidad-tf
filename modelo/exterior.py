"""Grafo exterior (ruta accesible del plano oficial). Coordenadas en pixeles del plano.png (1200x849)."""
import math

N = {}


def nodo(i, x, y, tipo, etiqueta=""):
    N[i] = (x, y, tipo, etiqueta)


# Entradas / salidas del campus
nodo("E_SUR", 143, 735, "entrada_campus", "Entrada Av. Alonso de Molina")
nodo("E_PRIM", 418, 278, "entrada_campus", "Entrada Av. Primavera")
nodo("S_EME", 756, 379, "salida_emergencia", "Salida de emergencia")

# Sur-oeste: acceso desde Av. Alonso de Molina, Tópico (22), pabellón 23
for i, x, y in [("s1", 157, 725), ("s2", 168, 708), ("s3", 175, 692), ("w1", 80, 694),
                ("w2", 107, 697), ("w3", 140, 695), ("u1", 190, 667), ("u2", 195, 645),
                ("u3", 195, 598), ("J_SW", 184, 576)]:
    nodo(i, x, y, "interseccion")
nodo("u_23", 195, 620, "interseccion")
nodo("A22", 97, 688, "ascensor", "Ascensor Tópico (22)")
nodo("P23", 166, 620, "entrada_accesible", "Pab. 23")

# Anillo frente a 19/20
nodo("J20W", 197, 670, "interseccion")
nodo("P20a", 231, 672, "entrada_accesible", "20")
nodo("P20b", 292, 672, "entrada_accesible", "20")
for i, x, y in [("L1", 227, 687), ("L2", 238, 703), ("L3", 260, 710), ("L4", 278, 703),
                ("L5", 293, 690), ("L6", 312, 668)]:
    nodo(i, x, y, "interseccion")

# Fila y=576 y sector 16/18
for i, x, y in [("r1", 220, 576), ("r2", 263, 576), ("r3", 338, 576), ("q1", 263, 609),
                ("q2", 263, 622), ("q4", 338, 622), ("V_E2", 338, 648)]:
    nodo(i, x, y, "interseccion")
nodo("P18", 254, 609, "entrada_accesible", "Pab. 18")
nodo("P16", 302, 620, "entrada_accesible", "Pab. 16")

# Curva oeste hacia 26/27
for i, x, y in [("c1", 180, 560), ("c2", 178, 537), ("J_26", 177, 508), ("c3", 152, 510),
                ("c4", 107, 523)]:
    nodo(i, x, y, "interseccion")
nodo("P26", 130, 518, "entrada_accesible", "Pab. 26")
nodo("P27", 97, 518, "entrada_accesible", "Pab. 27")
for i, x, y in [("d1", 187, 500), ("d2", 198, 488), ("d3", 205, 478), ("d4", 220, 468)]:
    nodo(i, x, y, "interseccion")

# Eje horizontal y~462 (con rampas)
nodo("H0", 228, 462, "interseccion")
nodo("R_a", 243, 456, "rampa", "R")
nodo("J250", 250, 461, "interseccion")
nodo("P_b", 256, 455, "entrada_accesible", "Pab. 28/29")
nodo("H1", 275, 461, "interseccion")
nodo("P_c", 294, 456, "entrada_accesible", "Pab. 29/30")
nodo("R_c", 302, 468, "rampa", "R")
nodo("H2", 340, 462, "interseccion")
nodo("H3", 383, 462, "interseccion")

# Eje vertical x=250 y ramales (sector 29/30/31/34)
for i, x, y in [("v1", 250, 430), ("J398", 250, 398), ("J386", 250, 386), ("vv", 250, 375),
                ("J352", 250, 352), ("h1", 288, 398), ("h2", 340, 398), ("k1", 297, 352),
                ("k2", 297, 318), ("m1", 200, 386), ("m2", 162, 386)]:
    nodo(i, x, y, "interseccion")
nodo("P29", 244, 375, "entrada_accesible", "Pab. 29")
nodo("P34", 288, 383, "entrada_accesible", "Pab. 34")
nodo("P31", 292, 340, "entrada_accesible", "Pab. 31")
nodo("A32", 304, 303, "ascensor", "Ascensor 32")

# Eje vertical oeste x~150 (sector 28/29)
for i, x, y in [("t2", 148, 326), ("n2", 148, 350), ("n3", 154, 370), ("n4", 154, 387),
                ("n5", 154, 410), ("n6", 154, 440)]:
    nodo(i, x, y, "interseccion")
nodo("Ph1", 135, 319, "entrada_accesible", "Pab. 30")
nodo("Ph2", 168, 319, "entrada_accesible", "Pab. 30")
nodo("P29w", 162, 363, "entrada_accesible", "Pab. 29")
nodo("P28", 146, 427, "entrada_accesible", "Pab. 28")
nodo("A28", 137, 455, "ascensor", "Ascensor 28")

# Rotonda grande (11): 12 nodos
CX, CY, RR = 462, 480, 64
for k in range(12):
    ang = math.radians(30 * k)
    nodo(f"RG{k}", round(CX + RR * math.cos(ang)), round(CY + RR * math.sin(ang)), "interseccion")

# Rampa hacia 15 (vertical x~382)
nodo("P_ramp", 403, 529, "entrada_accesible", "Rampa")
nodo("R_ramp", 404, 541, "rampa", "R")
for i, x, y in [("ramp_end", 393, 557), ("SV0", 383, 568), ("SV1", 382, 595), ("SV2", 382, 620),
                ("SV3", 388, 647)]:
    nodo(i, x, y, "interseccion")
nodo("P15", 393, 656, "entrada_accesible", "Pab. 15")
nodo("A15", 403, 667, "ascensor", "Ascensor 15")

# Salida inferior de la rotonda hacia 12/13/14
for i, x, y in [("X1", 497, 562), ("X2", 503, 578), ("X3", 553, 587), ("X4", 580, 603)]:
    nodo(i, x, y, "interseccion")
nodo("P12", 616, 626, "entrada_accesible", "Pab. 12")
nodo("R12", 605, 636, "rampa", "R")
nodo("A12", 639, 620, "ascensor", "Ascensor 12")

# Rotonda de la fuente: 8 nodos
FX, FY, FR = 508, 398, 27
for k in range(8):
    ang = math.radians(45 * k)
    nodo(f"F{k}", round(FX + FR * math.cos(ang)), round(FY + FR * math.sin(ang)), "interseccion")

# Acceso principal desde Av. Primavera
for i, x, y in [("e1", 415, 302), ("e2", 424, 313), ("e3", 443, 308), ("e4", 452, 322),
                ("e5", 466, 342), ("e6", 477, 360), ("e7", 484, 373)]:
    nodo(i, x, y, "interseccion")
nodo("P2", 448, 302, "entrada_accesible", "Pab. 2")

# Eje superior y=378 (hacia 3/4) y ramal inferior y=394 (hacia 8/9)
for i, x, y in [("T1", 560, 378), ("T2", 600, 378), ("T3", 660, 378), ("T4", 694, 378),
                ("T5", 747, 378)]:
    nodo(i, x, y, "interseccion")
nodo("P4", 605, 360, "entrada_accesible", "Pab. 4")
nodo("A4", 599, 342, "ascensor", "Ascensor 4")
nodo("P3", 694, 369, "entrada_accesible", "Pab. 3")
nodo("R3", 703, 369, "rampa", "R")
nodo("B1", 543, 395, "interseccion")
nodo("P9a", 565, 387, "entrada_accesible", "Pab. 9")
nodo("R9", 574, 387, "rampa", "R")
for i, x, y in [("B2", 592, 394), ("B3", 598, 398), ("B5", 643, 413), ("B6", 643, 427)]:
    nodo(i, x, y, "interseccion")
nodo("P8a", 630, 405, "entrada_accesible", "Pab. 8")
nodo("R8", 639, 405, "rampa", "R")
nodo("P8b", 632, 446, "entrada_accesible", "Pab. 8/9")

# Aristas: siguen la ruta accesible del plano
E = []


def cadena(*ids):
    for a, b in zip(ids, ids[1:]):
        E.append((a, b))


def dist(a, b):
    return math.hypot(N[a][0] - N[b][0], N[a][1] - N[b][1])


cadena("E_SUR", "s1", "s2", "s3", "u1", "u2", "u_23", "u3", "J_SW")
cadena("w1", "w2", "w3", "s3")
cadena("A22", "w2")
cadena("P23", "u_23")
cadena("u1", "J20W", "P20a", "L1", "L2", "L3", "L4", "L5", "P20b", "L6", "V_E2")
cadena("J_SW", "r1", "r2", "r3", "q4", "V_E2")
cadena("r2", "q1", "q2", "q4")
cadena("P18", "q1")
cadena("P16", "q2")
cadena("P16", "q4")
cadena("J_SW", "c1", "c2", "J_26", "c3", "P26", "c4", "P27")
cadena("J_26", "d1", "d2", "d3", "d4", "H0")
cadena("H0", "R_a", "J250", "P_b", "H1", "P_c", "R_c", "H2", "H3", "RG6")
cadena("J250", "v1", "J398", "J386", "vv", "J352", "k1", "k2", "A32")
cadena("P31", "k1")
cadena("P29", "vv")
cadena("J398", "h1", "h2")
cadena("P34", "h1")
cadena("J386", "m1", "m2", "n4")
cadena("t2", "n2", "n3", "n4", "n5", "n6")
cadena("Ph1", "t2", "Ph2")
cadena("P29w", "n3")
cadena("P28", "n5")
cadena("A28", "n6")

for k in range(12):
    E.append((f"RG{k}", f"RG{(k + 1) % 12}"))
for k in range(8):
    E.append((f"F{k}", f"F{(k + 1) % 8}"))

cadena("RG5", "P_ramp", "R_ramp", "ramp_end", "SV0", "SV1", "SV2", "SV3", "P15", "A15")
cadena("RG2", "X1", "X2", "X3", "X4", "P12")
cadena("R12", "P12", "A12")
cadena("E_PRIM", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "F5")
cadena("P2", "e3")
cadena("F2", "RG10")
cadena("F7", "T1", "T2", "T3", "T4", "T5", "S_EME")
cadena("P4", "T2")
cadena("A4", "P4")
cadena("P3", "T4")
cadena("R3", "T4")
cadena("F0", "B1", "P9a", "R9", "B2", "B3", "P8a", "R8", "B5", "B6", "P8b")
