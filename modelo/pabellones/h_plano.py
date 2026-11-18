"""
Pabellon H, pisos 1 a 5, reconstruido de las placas fotografiadas y anotadas por el equipo.
El marco de referencia es la foto del piso 4 (1600x1200), llevada a plano.png con un ajuste afin sobre 6 esquinas de la
huella (error maximo ~0.7 m). Los demas pisos se registran contra ese marco con las escaleras, el ascensor y las esquinas
del edificio, de modo que ejes y salas caen donde corresponde. Pasillo en L (sur + este) en los pisos 2 a 5; el piso 1 es
una plaza abierta (hall de ingreso) y trae su propio esqueleto. Una puerta por cada rectangulo marcado en la placa.
"""
from modelo.pabellones import plano_foto

_M = ((0.147034, -0.003137, 533.685484), (-0.000364, 0.147243, 371.802623))


def px(x, y):
    return (_M[0][0] * x + _M[0][1] * y + _M[0][2], _M[1][0] * x + _M[1][1] * y + _M[1][2])


CONTORNO = [(281, 287), (580, 565), (775, 563), (775, 292), (1360, 298), (1195, 976), (285, 998)]
HUELLAS = [[px(*p) for p in CONTORNO]]

# Puntos de control en el marco del piso 4: escalera norte, escalera central (rombo), escalera oeste, ascensor, esquinas
REF = dict(n=(925, 320), c=(755, 690), o=(305, 700), a=(915, 715), ne=(1360, 298), so=(285, 998), se=(1195, 976))


def _pares(**pts):
    return [(v, px(*REF[k])) for k, v in pts.items()]


PASILLO = [(330, 780), (410, 780), (535, 780), (730, 780), (760, 780), (850, 780), (915, 780), (958, 780), (1005, 780),
           (1005, 680), (1005, 642), (1005, 490), (1005, 452), (1005, 410), (1005, 380), (1005, 335), (1005, 316)]
VESTIBULO = [(410, 780), (410, 725), (410, 700), (410, 672), (432, 672)]

ESQ = dict(
    pares=[(p, px(*p)) for p in ((281, 287), (1360, 298), (1195, 976), (285, 998))],
    cadenas=[PASILLO, [(410, 780), (410, 700)]],
    accesos={"esc1": [(1005, 335), (965, 335), (925, 320)],
             "esc2": [(730, 780), (730, 740), (755, 690)],
             "esc3": [(410, 700), (345, 700), (305, 700)],
             "asc": [(915, 780), (915, 745), (915, 715)]},
    entradas=[("P8b", (565, 470)), ("P8b", (622, 470))])

_HALL = [(595, 520), (600, 545), (640, 620), (690, 690), (730, 735), (800, 735), (880, 735), (905, 735), (940, 735), (1010, 735)]
_ESTE = [(1010, 735), (1010, 650), (1010, 560), (1010, 480), (1010, 400), (1010, 330), (1010, 260)]

PISOS = {
    # Piso 1: plaza de ingreso con auditorio y laboratorio al oeste, salon central, salones al este y SSHH al sur
    1: dict(
        pares=_pares(n=(915, 205), c=(730, 600), o=(225, 620), a=(905, 640), ne=(1410, 182), se=(1215, 955)),
        esq=dict(
            cadenas=[_HALL, [(565, 470), (595, 520)], [(622, 470), (595, 520)], _ESTE],
            accesos={"esc1": [(1010, 260), (965, 240), (925, 210)],
                     "esc2": [(730, 735), (730, 690), (735, 610)],
                     "esc3": [(600, 545), (520, 600), (420, 650), (320, 670), (260, 650), (225, 620)],
                     "asc": [(905, 735), (905, 690), (905, 645)]},
            entradas=[("P8b", (565, 470)), ("P8b", (622, 470))]),
        salas=[("Salon/Laboratorio", (330, 460), [(525, 480)]), ("Auditorio Bancalari", (430, 760), [(585, 685)]),
               ("Salon H-16", (860, 500), [(976, 580)]), ("Oficina", (835, 258), [(967, 264)]),
               ("Salon H-15", (1160, 240), [(1045, 329)]), ("Salon H-14", (1135, 480), [(1052, 550)]),
               ("Salon H-13", (1140, 635), [(1054, 672)]), ("Salon H-12", (1140, 830), [(1029, 749)]),
               ("Salon H-11", (1170, 885), [(1068, 848)]),
               ("SSHH hombres", (795, 840), [(826, 776)]), ("SSHH mujeres", (930, 858), [(882, 780)])]),
    2: dict(
        pares=_pares(n=(910, 325), c=(738, 700), o=(232, 740), a=(905, 757), ne=(1357, 320), so=(205, 1075)),
        salas=[("Oficina", (845, 405), [(960, 412)]), ("Salon H-28", (855, 480), [(960, 504)]),
               ("Salon H-29", (880, 600), [(964, 692)]), ("Salon H-25", (1115, 400), [(1039, 472)]),
               ("Salon H-26", (1105, 570), [(1042, 669)]), ("Salon H-27", (1115, 795), [(1047, 830)]),
               ("Administracion", (1120, 940), [(992, 860)]), ("Administracion", (930, 955), [(930, 862)]),
               ("Oficina startups UPC 1", (260, 1000), [(264, 880)]), ("Oficina startups UPC 2", (430, 990), [(432, 870)]),
               ("Oficina startups UPC 3", (645, 995), [(651, 862)]), ("SSHH", (825, 925), [(844, 872)])]),
    3: dict(
        pares=_pares(n=(950, 305), c=(785, 688), o=(262, 715), a=(948, 735), ne=(1410, 290), so=(230, 1062)),
        salas=[("Oficina", (855, 350), None), ("Salon H-38", (905, 580), [(1004, 688)]),
               ("Salon H-37", (1140, 360), [(1085, 438)]), ("Salon H-36", (1155, 505), [(1084, 564)]),
               ("Salon H-35", (1165, 725), [(1091, 708)]), ("Salon H-34", (1145, 985), [(1045, 846)]),
               ("Salon H-33", (695, 1000), [(773, 846)]), ("Salon H-32", (535, 1005), [(589, 848)]),
               ("Salon H-31", (350, 935), [(403, 858)]), ("Salon H-30", (505, 725), [(354, 745)]),
               ("Administracion", (295, 600), [(336, 654)]), ("SSHH", (890, 950), [(886, 862)])]),
    4: dict(
        pares=ESQ["pares"],
        esq=dict(cadenas=[PASILLO, VESTIBULO]),
        salas=[("Salon/Lab. software entretenimiento H-40", (365, 520), [(432, 641)]), ("Salon/Lab. computo H-41", (418, 905), [(535, 810)]),
               ("Salon H-42", (665, 905), [(760, 808)]), ("Salon/Taller de diseno H-43", (1050, 905), [(958, 807)]),
               ("Salon H-44", (1130, 735), [(1040, 680)]), ("Salon/Lab. computo H-45", (1140, 560), [(1040, 490), (1040, 642)]),
               ("Salon/Taller de diseno H-46", (1170, 385), [(1040, 316), (1040, 452)]), ("Salon H-47", (865, 540), [(970, 410)]),
               ("Sala de servidores", (512, 640), [(445, 725)]), ("SSHH hombres", (815, 915), [(825, 800)]),
               ("SSHH mujeres", (890, 915), [(875, 800)]), ("Oficina PTC", (840, 345), [(970, 380)])]),
    5: dict(
        pares=_pares(n=(958, 248), c=(793, 573), o=(388, 598), a=(940, 612), ne=(1368, 230), so=(355, 860)),
        extras=[[(1026, 700), (1026, 780), (1026, 846)]],
        salas=[("Salon/Lab. diseno de software H-51", (428, 497), [(488, 531)]), ("Salon/Lab. MAC H-50", (570, 607), [(502, 609)]),
               ("Salon/Lab. computo H-52", (558, 733), [(575, 693)]), ("Salon H-53", (638, 830), [(612, 695)]),
               ("Salon/Capstone ing. sistemas H-54", (755, 818), [(798, 698)]), ("Salon/Aula acustica comunicaciones H-55", (1110, 845), [(1002, 846), (1053, 846)]),
               ("Salon/Lab. computo H-56", (1098, 632), [(1060, 590)]), ("Salon/Ambiente disponible H-57", (1095, 490), [(1064, 410), (1060, 540)]),
               ("Salon/Lab. computo H-58", (1105, 345), [(1067, 249), (1064, 372)]), ("Salon/Lab. fisica H-59", (925, 553), [(996, 570)]),
               ("Almacen", (860, 265), None), ("Sala de electricidad", (945, 735), [(958, 699)]),
               ("SSHH hombres", (850, 790), [(864, 722)]), ("SSHH mujeres", (915, 790), [(896, 725)]),
               ("Administracion", (1030, 748), [(1008, 714)]), ("Almacen", (1030, 805), [(1008, 787)]),
               ("Administracion", (960, 820), [(972, 820)])]),
}


# Banos de H: siempre dos zonas separadas con puerta propia (hombres, mujeres), en la misma posicion en todos los pisos.
# Se toman de la placa del piso 4 y se llevan a la foto de cada piso.
_Y_PUERTA = {2: 872, 3: 862}   # altura de la puerta marcada por el equipo en cada placa
_SSHH = (("SSHH hombres", (815, 915), (825, 800)), ("SSHH mujeres", (890, 915), (875, 800)))


def _banos(piso):
    inv = plano_foto.ajustar([(q, pt) for pt, q in PISOS[piso]["pares"]])
    f = lambda pt: tuple(round(v) for v in inv(*px(*pt)))
    return [(n, f(c), [(f(d)[0], _Y_PUERTA[piso])]) for n, c, d in _SSHH]


for _p in (2, 3):
    PISOS[_p]["salas"] = [x for x in PISOS[_p]["salas"] if not x[0].startswith("SSHH")] + _banos(_p)
