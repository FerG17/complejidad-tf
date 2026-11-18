"""
Pabellon D, pisos 1 a 5, reconstruido de las placas fotografiadas y anotadas por el equipo.
Las fotos estan giradas 90 grados en sentido horario respecto de plano.png (arriba de la foto = este, hacia C; derecha = sur).
Marco de referencia: foto del piso 1, a 0.141 px de plano por px de foto; el ascensor de la placa cae sobre el nodo exterior
A28 del plano. Los demas pisos se registran con las esquinas del bloque oeste (aulas 14/15), el ascensor y la escalera.
Las placas de los pisos 4 y 5 son la misma planta tipica (ambas dicen "quinto piso"): se modelan con los numeros del piso.
El enlace con C es el extremo norte del pasaje oeste.
"""
from modelo.pabellones import plano_foto

_P = [((205, 325), (141, 292)), ((1315, 325), (141, 448.5)), ((205, 740), (82.5, 292))]
_F1 = plano_foto.ajustar(_P)
REF = dict(tl=(205, 325), bl=(205, 740), a=(1345, 350), e=(1400, 510))


def _pares(**pts):
    return [(v, _F1(*REF[k])) for k, v in pts.items()]


ESQ = dict(
    pares=_P,
    cadenas=[[(410, 535), (500, 535), (600, 535), (755, 535), (850, 535), (1020, 535), (1150, 535), (1230, 535), (1300, 535)],
             [(410, 330), (410, 430), (410, 535), (410, 620), (410, 700)],
             [(1230, 535), (1230, 460), (1230, 400)]],
    accesos={"esc1": [(1300, 535), (1360, 520), (1405, 510)],
             "asc": [(1300, 535), (1300, 440), (1345, 350)]},
    inicio=(410, 330), fin=(1300, 535),
    entradas=[("P28", (1230, 400))], asc_ext="A28")


PISOS = {
    1: dict(
        pares=_P,
        salas=[("Salon D-14", (330, 415), [(390, 510)]), ("Salon D-15", (340, 665), [(390, 552)]),
               ("Salon/Lab. MAC D-13", (540, 350), [(596, 499)]), ("Salon/Lab. MAC D-12", (720, 380), [(634, 496)]),
               ("Salon/Lab. MAC D-11", (940, 380), [(850, 498)]), ("Oficina creatividad empresarial", (1095, 440), [(1164, 486)]),
               ("Salon/Lab. computo D-16", (475, 630), [(594, 572)]), ("Salon/Lab. computo D-17", (660, 620), [(809, 570)]),
               ("Salon/Lab. computo D-18", (935, 600), [(1024, 569)]), ("Salon/Lab. computo D-19", (1170, 620), [(1265, 568)])]),
    2: dict(
        modelo="sim",
        pares=_pares(tl=(110, 315), bl=(110, 740), a=(1300, 375), e=(1380, 510)),
        salas=[("Salon D-23", (480, 365), [(506, 496)]), ("Salon D-22", (655, 360), [(738, 499)]),
               ("Salon/Lab. MAC D-21", (845, 360), [(958, 502)]), ("SSHH discapacitados", (1055, 360), [(1048, 468)]),
               ("Oficina creatividad empresarial", (1180, 390), [(1220, 446), (1148, 460)]),
               ("Salon D-24", (195, 395), [(296, 510)]), ("Salon D-25", (195, 650), [(296, 545)]),
               ("Salon D-26", (430, 610), [(507, 566)]), ("Salon/Lab. computo D-27", (635, 610), [(736, 578)]),
               ("Salon D-28", (835, 610), [(926, 575)]), ("Salon/Lab. MAC D-29", (1110, 620), [(1005, 576)])]),
    3: dict(
        modelo="sim",
        pares=_pares(tl=(140, 497), bl=(140, 905), a=(1318, 550), e=(1395, 660)),
        salas=[("Salon D-33", (480, 555), [(532, 669)]), ("Salon D-32", (655, 570), [(722, 670)]),
               ("Salon/Lab. MAC D-31", (870, 570), [(962, 664)]), ("SSHH", (1060, 550), [(1068, 637)]),
               ("Oficina", (1215, 530), [(1132, 668), (1165, 620)]),
               ("Salon D-34", (240, 570), [(319, 690)]), ("Salon D-35", (245, 815), [(319, 725)]),
               ("Salon D-36", (440, 800), [(532, 740)]), ("Salon/Lab. computo D-37", (630, 790), [(756, 737)]),
               ("Salon/Lab. MAC D-38", (855, 795), [(980, 736)]), ("Salon/Lab. MAC D-39", (1160, 800), [(1017, 738)])]),
    4: dict(
        modelo="sim",
        pares=_pares(tl=(105, 303), bl=(105, 762), a=(1400, 380), e=(1445, 510)),
        salas=[("Salon D-43", (445, 350), [(534, 500)]), ("Salon D-42", (645, 355), [(788, 508)]),
               ("Salon D-41", (880, 355), [(994, 511)]), ("SSHH", (1105, 365), [(1092, 516)]),
               ("Oficina", (1255, 360), [(1224, 466)]),
               ("Salon D-44", (190, 405), [(304, 510)]), ("Salon D-45", (190, 685), [(304, 562)]),
               ("Salon D-46", (440, 625), [(536, 580)]), ("Salon/Lab. computo D-47", (660, 625), [(780, 586)]),
               ("Salon D-48", (890, 625), [(985, 584)]), ("Salon/Lab. MAC D-49", (1215, 630), [(1070, 588)])]),
    5: dict(
        modelo="sim",
        pares=_pares(tl=(80, 415), bl=(80, 845), a=(1322, 455), e=(1395, 590)),
        salas=[("Salon D-53", (430, 455), [(484, 593)]), ("Salon D-52", (590, 465), [(722, 593)]),
               ("Salon D-51", (840, 480), [(921, 596)]), ("SSHH", (1040, 480), [(1048, 565), (1114, 594)]),
               ("Oficina", (1205, 465), [(1200, 531), (1149, 551)]),
               ("Salon D-54", (190, 490), [(269, 610)]), ("Salon D-55", (160, 720), [(269, 655)]),
               ("Salon D-56", (370, 720), [(486, 660)]), ("Salon/Lab. computo D-57", (610, 735), [(714, 667)]),
               ("Salon D-58", (820, 720), [(920, 673)]), ("Salon/Lab. MAC D-59", (1150, 740), [(997, 672)])]),
}
