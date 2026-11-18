"""
Pabellon J, pisos 1 a 5, reconstruido de las placas de evacuacion fotografiadas y anotadas por el equipo.
Marco de referencia: foto del piso 2 (esquinas NO/NE/SO ajustadas a la huella gris de plano.png). Los demas pisos se
registran contra ese marco con las escaleras, el ascensor y la esquina noroeste. Pasillo central este-oeste con la salida
al pasaje J-B en su extremo este; el piso 1 (banco y oficinas) trae su propio esqueleto.
"""
from modelo.pabellones import plano_foto

_P = [((290, 288), (222, 291)), ((1385, 300), (301, 291)), ((515, 962), (240, 345))]
_F = plano_foto.ajustar(_P)

REF = dict(w=(400, 780), e1=(1190, 450), e2=(1215, 745), a=(1320, 335), nw=(290, 288), sw=(515, 962))


def _pares(**pts):
    return [(v, _F(*REF[k])) for k, v in pts.items()]


ESQ = dict(
    pares=_P,
    cadenas=[[(520, 632), (565, 632), (770, 632), (990, 632), (1140, 632), (1235, 632)]],
    accesos={"esc1": [(1140, 632), (1180, 590), (1190, 450)],
             "esc2": [(1235, 632), (1235, 690), (1215, 745)],
             "esc3": [(520, 632), (520, 690), (400, 780)],
             "asc": [(1235, 632), (1290, 600), (1300, 420), (1320, 335)]},
    inicio=(520, 632), fin=(1235, 632), asc_ext="A32")

_AISLAS = [[(x, 470), (x, 626)] for x in (565, 770, 990)] + [[(x, 638), (x, 832)] for x in (565, 770, 990)]

PISOS = {
    1: dict(
        pares=_pares(w=(380, 790), e2=(1230, 745), a=(1222, 365), nw=(262, 285)),
        esq=dict(
            cadenas=[[(527, 905), (527, 770), (527, 640), (527, 570), (700, 557), (865, 557), (865, 700), (865, 815), (1000, 815), (1160, 815)],
                     [(865, 557), (865, 500), (818, 500), (721, 500)],
                     [(1160, 480), (1160, 560), (1160, 640), (1160, 740), (1160, 815), (1160, 900), (1165, 950)]],
            accesos={"esc1": [(1160, 560), (1148, 500), (1135, 460)],
                     "esc2": [(1160, 740), (1200, 745), (1230, 745)],
                     "esc3": [(527, 770), (470, 775), (380, 790)],
                     "asc": [(1160, 480), (1205, 440), (1222, 365)]},
            inicio=(527, 640), fin=(1160, 815), entradas=[("P31", (1165, 950))]),
        salas=[("Oficina", (530, 410), [(721, 489)]), ("Oficina", (780, 330), [(818, 436)]),
               ("Oficina", (895, 325), [(872, 432)]), ("Vida universitaria / oport. laborales", (985, 455), [(891, 466), (1082, 636)]),
               ("Almacen", (1120, 380), [(1108, 462)]), ("SSHH mujeres", (425, 350), [(408, 494)]),
               ("SSHH hombres", (330, 430), [(377, 516)]), ("SSHH 3", (325, 595), [(381, 617)]),
               ("Sala de electricidad", (430, 690), [(466, 646)]), ("Banco Interbank", (700, 830), [(602, 904)])]),
    2: dict(
        pares=_P,
        extras=_AISLAS,
        salas=[("Oficina", (618, 350), [(576, 460)]), ("Oficina", (760, 360), [(780, 460)]),
               ("Oficina", (920, 360), [(958, 460)]), ("Oficina", (1085, 350), [(1015, 462)]),
               ("Oficina", (660, 505), [(714, 598)]), ("Oficina", (865, 510), [(917, 599)]),
               ("Oficina", (675, 745), [(712, 662)]), ("Oficina", (865, 745), [(904, 668)]),
               ("Oficina", (1080, 745), [(1097, 650)]), ("Oficina", (600, 905), [(572, 832)]),
               ("Oficina", (750, 910), [(769, 829)]), ("Oficina", (925, 915), [(958, 833)]),
               ("Oficina", (1085, 915), [(1010, 833)]),
               ("SSHH hombres", (345, 470), [(383, 579)]), ("SSHH mujeres", (455, 470), [(443, 574)]),
               ("Sala de comunicaciones", (325, 600), [(352, 592)]), ("Sala de electricidad", (445, 680), [(458, 639)])]),
    3: dict(
        pares=_pares(w=(390, 760), e1=(1190, 430), e2=(1195, 745), a=(1293, 325), nw=(287, 287), sw=(500, 968)),
        salas=[("Oficina", (985, 320), [(1090, 452)]), ("Oficina", (1015, 490), [(968, 560)]),
               ("Oficina", (600, 745), [(667, 796)]), ("Gobierno Campus", (825, 730), [(765, 646), (907, 644)]),
               ("Director ejecutivo", (630, 890), [(734, 824)]), ("Gerente de operaciones", (915, 885), [(867, 812)]),
               ("Director", (1065, 885), [(1012, 789)]), ("SSHH hombres", (330, 400), [(370, 523)]),
               ("SSHH mujeres", (445, 410), [(418, 520)]), ("Sala de comunicaciones", (310, 610), [(346, 580)]),
               ("Sala de electricidad", (435, 655), [(444, 622)])]),
    4: dict(
        pares=_pares(w=(285, 770), e1=(1195, 410), e2=(1195, 740), a=(1305, 285), nw=(165, 205), sw=(425, 985)),
        salas=[("SSHH hombres", (260, 375), [(276, 450)]), ("SSHH mujeres", (365, 360), [(340, 454)]),
               ("Sala de electricidad", (265, 570), [(310, 528)]), ("Oficina PTC", (700, 760), None)]),
    5: dict(
        pares=_pares(w=(410, 780), e1=(1255, 440), e2=(1290, 760), a=(1385, 330), nw=(315, 285), sw=(550, 985)),
        extras=[[(740, 483), (740, 628)], [(1020, 483), (1020, 628)]],
        salas=[("Oficina", (655, 340), [(706, 405)]), ("Oficina", (815, 340), [(765, 406)]),
               ("Oficina", (940, 350), [(1005, 413)]), ("Oficina", (1110, 350), [(1064, 410)]),
               ("Oficina", (1145, 440), [(1104, 582)]), ("Sala de reuniones", (630, 495), [(706, 583)]),
               ("Asesoria de riesgo", (860, 470), [(768, 482), (912, 588)]),
               ("Oficina PTC", (700, 795), [(938, 674)]), ("SSHH hombres", (375, 400), [(410, 513)]),
               ("SSHH mujeres", (505, 405), [(472, 514)]), ("Sala de electricidad", (395, 630), [(446, 584)])]),
}
