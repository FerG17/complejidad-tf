"""
Pabellon A (con Aula Magna), pisos 1 a 5, reconstruido de las placas EV-M-01 fotografiadas y anotadas por el equipo.
Marco de referencia: foto del piso 1, llevada a plano.png con la conversion (205 + (x-120)*0.154, 618 + (y-565)*0.154)
calibrada con las puertas P16 y P18. Las demas placas se registran con las cuatro esquinas del bloque central de aulas.
Oval oeste (Aula Magna), hall con la escalera 1, bloque central de 4 aulas sobre el cruce de circulacion E-O y circulacion
N-S al este con la escalera 2. No tiene ascensor: solo el piso 1 es accesible. Numeracion de aulas tal como la rotulo el equipo.
"""
from modelo.pabellones import plano_foto

K = 0.154


def cp(x, y):
    return 205 + (x - 120) * K, 618 + (y - 565) * K


_BLOQUE = dict(tl=(563, 365), tr=(1022, 358), bl=(562, 795), br=(1022, 795))


def _pares(**pts):
    return [(v, cp(*_BLOQUE[k])) for k, v in pts.items()]


ESQ = dict(
    pares=[(v, cp(*v)) for v in ((470, 585), (1062, 340), (1062, 830))],
    cadenas=[[(470, 585), (550, 585), (660, 585), (790, 585), (900, 585), (1062, 585)],
             [(1062, 340), (1062, 500), (1062, 585), (1062, 700), (1062, 830)]],
    accesos={"esc1": [(470, 585), (490, 700)], "esc2": [(1062, 340), (1160, 345)]},
    entradas=[("P16", (790, 585), "supuesto: P16 entra al cruce de circulacion"),
              ("P18", (470, 585), "supuesto: P18 entra al hall escalera"),
              ("V_E2", (1062, 830), "supuesto: V_E2 = salida sur de la circulacion N-S")])

_AM = "Aula Magna"

PISOS = {
    1: dict(
        pares=ESQ["pares"],
        salas=[(_AM, (250, 525), [(385, 455)]), ("Salon A-12", (655, 430), [(742, 545)]), ("Salon A-11", (910, 435), [(832, 545)]),
               ("Salon A-14", (660, 715), [(738, 628)]), ("Salon A-13", (935, 715), [(832, 625)]),
               ("Salon A-16", (1185, 470), [(1100, 560)]), ("Salon A-15", (1195, 690), [(1098, 692)])]),
    2: dict(
        pares=_pares(tl=(597, 402), tr=(1058, 400), bl=(600, 850), br=(1060, 835)),
        salas=[(_AM + " - nivel intermedio", (300, 570), None), ("Salon A-23", (710, 475), [(780, 580)]),
               ("Salon A-24", (955, 490), [(878, 578)]), ("Salon A-21", (710, 755), [(782, 670)]),
               ("Salon A-22", (950, 765), [(878, 665)]), ("Salon A-25", (1225, 505), [(1138, 607)]),
               ("SSHH mujeres", (1250, 686), [(1160, 720)]), ("SSHH hombres", (1255, 790), [(1180, 790)])]),
    3: dict(
        pares=_pares(tl=(553, 440), tr=(1028, 438), bl=(555, 890), br=(1027, 885)),
        salas=[(_AM + " - nivel superior", (200, 605), [(376, 538)]), ("Salon A-33", (700, 545), [(746, 624)]),
               ("Salon A-34", (935, 540), [(842, 627)]), ("Salon A-31", (675, 810), [(746, 720)]),
               ("Salon A-32", (905, 815), [(838, 717)]), ("Salon A-36", (1190, 580), [(1120, 532)]),
               ("Salon A-35", (1205, 780), [(1120, 800)])]),
    4: dict(
        pares=_pares(tl=(535, 433), tr=(1008, 428), bl=(528, 885), br=(1020, 880)),
        salas=[("Salon A-43", (655, 520), [(726, 614)]), ("Salon A-44", (920, 520), [(828, 618)]),
               ("Salon A-41", (635, 800), [(728, 714)]), ("Salon A-42", (915, 800), [(824, 713)]),
               ("Salon A-46", (1210, 525), [(1110, 524)]), ("Salon A-45", (1215, 695), [(1110, 656)]),
               ("SSHH hombres", (1230, 820), [(1144, 792)]), ("SSHH mujeres", (1240, 865), [(1146, 847)])]),
    5: dict(
        pares=_pares(tl=(585, 428), tr=(1045, 423), bl=(585, 865), br=(1050, 860)),
        extras=[[(470, 625), (455, 720), (420, 820), (345, 868)]],
        salas=[("GEA", (290, 485), [(420, 518)]), ("Set de fotografia", (290, 645), None),
               ("Almacen de audiovisuales", (245, 800), [(322, 874)]), ("Maquillaje", (355, 800), [(322, 874)]),
               ("Salon A-53", (720, 500), [(768, 598)]), ("Salon A-54", (955, 495), [(863, 601)]),
               ("Salon A-51", (710, 795), [(770, 696)]), ("Salon A-52", (945, 780), [(864, 695)]),
               ("Salon A-56", (1230, 540), [(1140, 634)]), ("Salon A-55", (1228, 750), [(1141, 774)])]),
}
