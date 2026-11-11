"""Constantes del modelo del campus y rutas del proyecto."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
PLANO = DATOS / "plano.png"
CAPTURAS = RAIZ / "capturas"

ESCALA = 0.275        # metros por pixel del plano
ALTO_PISO = 3.5       # metros entre pisos
ESPACIADO = 1.5       # metros entre nodos consecutivos de un pasillo
COSTO_ESCALERA = 3.0  # una escalera cuesta 3x el desnivel (esfuerzo)
COSTO_ASCENSOR = 8.0  # penalizacion fija por esperar/usar el ascensor (en metros equivalentes)

BASE_Z = {p: 0.0 for p in "ABCDEFGHIJ"}   # el campus tiene pendiente: todos parten de z = 0
