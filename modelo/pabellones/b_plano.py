"""
Pabellon B, pisos 1 a 5, reconstruido de las placas de riesgos fotografiadas y anotadas por el equipo.
Las fotos estan giradas 90 grados respecto de plano.png (arriba de la foto = este del plano; la izquierda de la foto = norte).
Marco de referencia: foto del piso 3, ajustada a la huella gris con tres esquinas. Los demas pisos se registran con el
ascensor-enlace a J y las tres escaleras comunes (SO, centro, SE); los pisos 1 y 2 traen su propio esqueleto porque tienen
un anexo este (escalera NE y escalera E) que los pisos superiores no tienen. El "asc" de la placa es el enlace con el
ascensor de J: B no tiene ascensor propio.
"""
from modelo.pabellones import plano_foto

_P = [((390, 292), (370, 283)), ((1275, 300), (370, 393)), ((392, 838), (310, 283))]
_F3 = plano_foto.ajustar(_P)
REF = dict(a=(478, 882), so=(470, 985), c=(730, 960), se=(1105, 895), tr=(1275, 300))


def _pares(**pts):
    return [(v, _F3(*REF[k])) for k, v in pts.items()]


_PASILLO = [(560, 560), (640, 560), (700, 560), (855, 560), (1000, 560), (1100, 560), (1210, 560)]
_ESTE = [(1210, 560), (1210, 700), (1200, 830)]
_PASAJE = [(560, 560), (560, 640), (560, 720), (560, 800), (560, 870)]

ESQ = dict(
    pares=_P,
    cadenas=[_PASILLO, _ESTE, _PASAJE, [(560, 870), (480, 880)], [(560, 870), (620, 880)]],
    accesos={"esc1": [(560, 870), (520, 930), (485, 970)],
             "esc2": [(620, 880), (660, 900), (735, 950)],
             "esc3": [(1200, 830), (1160, 880), (1105, 895)]},
    inicio=(480, 880), fin=(1210, 560),
    entradas=[("P34", (1200, 830))])

_F2 = plano_foto.semejanza(_pares(a=(340, 855), so=(335, 930), c=(570, 935), se=(905, 885)))

PISOS = {
    1: dict(
        modelo="sim",
        pares=[((365, 823), _F3(*REF["a"])), ((620, 900), _F3(*REF["c"])), ((1210, 325), _F2(1160, 370)), ((1300, 830), _F2(1255, 810))],
        esq=dict(
            cadenas=[[(285, 525), (400, 525), (580, 525), (760, 525), (940, 525), (1100, 525), (1210, 525)],
                     [(1210, 330), (1210, 430), (1210, 525), (1210, 620), (1210, 720), (1210, 830), (1210, 860), (1205, 950)],
                     [(1210, 860), (1060, 880), (870, 875), (700, 880), (560, 885), (500, 930), (420, 880), (365, 860)]],
            accesos={"esc2": [(560, 885), (600, 895), (620, 900)],
                     "esc4": [(1210, 430), (1210, 360), (1210, 325)],
                     "esc5": [(1210, 830), (1260, 830), (1300, 830)]},
            inicio=(365, 860), fin=(1210, 525), entradas=[("P34", (1205, 950))]),
        salas=[("Salon B-12", (470, 370), [(513, 478)]), ("Salon B-11", (730, 370), [(828, 476)]),
               ("Salon B-10", (1050, 350), [(920, 476)]), ("Salon B-13", (310, 690), [(443, 579)]),
               ("Salon B-14", (590, 690), [(702, 574)]), ("Salon B-15", (900, 690), [(886, 575)]),
               ("Cuarto de limpieza", (1050, 640), [(1049, 578)]), ("Espacio disponible 1", (1115, 630), [(1136, 574)]),
               ("Almacen", (1340, 395), [(1288, 427)]), ("Almacen", (1345, 465), [(1276, 486)]),
               ("Sala de seguridad 2", (1330, 575), [(1273, 666)]), ("Almacen", (960, 875), [(1025, 914)]),
               ("Centro de operaciones campus-soporte", (1095, 870), [(1124, 944)]),
               ("Sala de seguridad 1", (270, 355), None), ("Sala de objetos perdidos", (235, 520), None),
               ("Administracion", (385, 910), [(470, 933)])]),
    2: dict(
        modelo="sim",
        pares=_pares(a=(340, 855), so=(335, 930), c=(570, 935), se=(905, 885)),
        esq=dict(
            cadenas=[[(260, 548), (312, 548), (375, 548), (500, 548), (650, 548), (800, 548), (950, 548), (1050, 548), (1100, 548)],
                     [(312, 330), (312, 420), (312, 548)],
                     [(375, 548), (375, 640), (375, 720), (375, 810), (375, 870)], [(375, 870), (335, 860)],
                     [(1050, 548), (1050, 640), (1050, 720), (1050, 800), (1040, 870)],
                     [(1100, 548), (1100, 420), (1160, 380)], [(375, 870), (500, 880)],
                     [(1050, 720), (1100, 730), (1150, 740)]],
            accesos={"esc1": [(375, 870), (350, 905), (335, 930)],
                     "esc2": [(500, 880), (540, 910), (570, 935)],
                     "esc3": [(1040, 870), (960, 880), (905, 885)],
                     "esc4": [(1100, 420), (1130, 395), (1160, 370)],
                     "esc5": [(1150, 740), (1200, 740), (1255, 810)]},
            inicio=(335, 860), fin=(1100, 548)),
        salas=[("Oficina de asesores 1", (240, 315), [(299, 386)]), ("Oficina de asesores 2", (230, 420), [(300, 470)]),
               ("SSHH hombres", (385, 455), [(425, 508)]), ("Salon B-22", (615, 335), [(556, 508)]),
               ("Salon B-21", (865, 395), [(918, 506)]), ("Oficina", (1050, 395), [(997, 408), (1018, 489)]),
               ("SSHH mujeres", (255, 665), [(276, 590)]), ("Salon B-25", (595, 640), [(672, 598)]),
               ("Salon B-26", (870, 675), [(908, 605)]),
               ("Direccion de Inteligencia e Innovacion Digital", (1165, 840), [(1119, 725), (1125, 936)]),
               ("Almacen", (1055, 935), [(1097, 893)])]),
    3: dict(
        pares=_P,
        salas=[("Salon B-34", (585, 455), [(622, 508)]), ("Salon B-33", (795, 475), [(700, 519)]),
               ("Salon B-32", (990, 440), [(1038, 505)]), ("Salon B-31", (1180, 425), [(1105, 516)]),
               ("SSHH mujeres", (485, 603), [(534, 540)]), ("SSHH hombres", (480, 760), [(532, 690)]),
               ("Salon B-35", (740, 660), [(843, 618)]), ("Salon B-36", (1000, 665), [(926, 608)])]),
    4: dict(
        modelo="sim",
        pares=_pares(a=(395, 880), so=(395, 965), c=(650, 950), se=(1040, 905), tr=(1208, 298)),
        salas=[("Salon B-43", (465, 375), [(626, 512)]), ("Salon B-42", (755, 335), [(894, 508)]),
               ("Salon B-41", (1095, 395), [(980, 510)]), ("Salon B-44", (640, 660), [(754, 615)]),
               ("Salon B-45", (935, 655), [(1032, 606)]), ("SSHH mujeres", (400, 590), [(470, 532)]),
               ("SSHH hombres", (395, 770), [(464, 678)])]),
    5: dict(
        modelo="sim",
        pares=_pares(a=(410, 870), so=(400, 940), c=(630, 915), se=(1050, 900), tr=(1272, 243)),
        salas=[("Salon B-53", (610, 285), [(708, 478)]), ("Salon B-52", (805, 285), [(918, 478)]),
               ("Salon B-51", (1150, 330), [(1016, 482)]), ("Salon B-54", (640, 630), [(776, 592)]),
               ("Salon B-55", (945, 620), [(1079, 578)]), ("Comedor/Terraza 1", (370, 380), [(446, 536)]),
               ("Comedor/Terraza 2", (380, 745), [(445, 706)])]),
}
