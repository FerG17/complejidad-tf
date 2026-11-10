# Campus Monterrico 3D - rutas accesibles (BFS + A*)
Equipo 10 - 1ACC0184 Complejidad Algoritmica

    pip install -r requirements.txt
    python app.py            # ventana interactiva
    python app.py --prueba   # escenario de ejemplo: abre la ventana unos segundos y guarda capturas en capturas/
    python generador.py      # regenera datos/nodos.csv y datos/aristas.csv

Buscador: en la ventana escribe en Origen/Destino y/o filtra por pabellon y piso. Entiende sinonimos y codigos de aula:
"salon 51", "e 51", "quinto piso aula 1", "bano piso 3", "labs computo c", "cub 54", "kata"; tambien: python buscador.py "salon 51".
Escala: 0.275 m/px (calibrada con Google Maps).

Archivos: exterior.py (ruta accesible del plano), generador.py (pabellones + conexiones + CSV),
algoritmos.py (BFS y A* a mano), simulador.py (logica), ascensores.py (catalogo de ascensores y retos),
buscador.py (busqueda por nombre),
vista.py (plano 2D + 3D con OpenGL, pyqtgraph), app.py (ventana, PySide6).
Los ver_*.py (figuras para el informe) usan matplotlib. Ejecutable: construir_exe.bat (PyInstaller, sin probar).

Supuestos editables en generador.py: ESCALA (m/px), BASE_Z, ESPACIADO, PAB (geometria de cascarones),
PASAJES (J-B, C-D, E-F, F-G). Las aristas supuestas llevan nota en aristas.csv.
Pabellones A-J modelados con salas y puertas (nodos). K y L pendientes. Nombres "(aprox)": numero no legible en las placas.

## Como ejecutar (rapido)
Windows: doble clic a EJECUTAR.bat  |  Mac/Linux: ./ejecutar.sh
Manual: pip install -r requirements.txt  y luego  python app.py
Vistas extra: python ver_campus.py | python ver_pabellon.py H | python app.py --prueba

## Ventana (v3, pyqtgraph + OpenGL)
Vista 3D: Auto (sigue la ruta y hace zoom en los pabellones que usa) / Campus completo / un pabellon.
Cada pabellon es un edificio cerrado: muros por piso, columnas en las esquinas y techo (la Biblioteca es un cilindro);
el plano del campus hace de suelo. Los pabellones que no se ven por dentro quedan como masas tenues.
"Piso en 3D": Todos o un solo piso. Cada piso tiene su color (ver leyenda). "Muros" se puede apagar.
Ascensores: pestana "Ascensores y retos". Marcar un ascensor lo saca de servicio (todos sus pisos); si la ruta lo usa, A* recalcula.
El boton "Ascensor fuera de servicio" saca el siguiente ascensor de la ruta mientras se camina. Los retos cargan escenarios
(p. ej. G sin ascensor: la ruta cambia por E y F; J o D sin ascensor: pisos altos aislados; Biblioteca con un solo ascensor).
Plano 2D: muestra el piso elegido ("Piso en el plano"); clic izquierdo = origen, clic derecho = destino sobre ese piso.
"El plano sigue al caminante" cambia el piso del plano mientras recorre la ruta.
3D con el mouse: arrastrar = rotar, rueda = zoom, boton central o Ctrl+arrastrar = mover.
Busqueda: escribe en Origen/Destino y/o elige pabellon y piso; clic en un resultado, o Enter para el primero.
Atajos: espacio = iniciar, b = barrera en el tramo, a = ascensor fuera de servicio, r = reiniciar.
