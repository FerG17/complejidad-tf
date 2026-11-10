# Campus Monterrico 3D - rutas accesibles (BFS + A*)
Equipo 10 - 1ACC0184 Complejidad Algoritmica

    pip install -r requirements.txt
    python app.py            # ventana interactiva
    python app.py --prueba   # capturas de ejemplo en capturas/
    python generador.py      # regenera datos/nodos.csv y datos/aristas.csv

Buscador: en la ventana escribe el nombre en Origen/Destino (ej. "cub 54", "aula a-34", "sshh I p3", "kata"); tambien: python buscador.py "cub 54".
Escala: 0.275 m/px (calibrada con Google Maps).

Archivos: exterior.py (ruta accesible del plano), generador.py (pabellones + conexiones + CSV),
algoritmos.py (BFS y A* a mano), simulador.py (logica), vista.py (2D+3D), app.py (ventana).
Ejecutable: construir_exe.bat (PyInstaller).

Supuestos editables en generador.py: ESCALA (m/px), BASE_Z, ESPACIADO, PAB (geometria de cascarones),
PASAJES (J-B, E-F, F-G). Las aristas supuestas llevan nota en aristas.csv.
Pabellones A-J modelados con salas y puertas (nodos). K y L pendientes. Nombres "(aprox)": numero no legible en las placas.

## Como ejecutar (rapido)
Windows: doble clic a EJECUTAR.bat  |  Mac/Linux: ./ejecutar.sh
Manual: pip install -r requirements.txt  y luego  python app.py
Vistas extra: python ver_campus.py | python ver_pabellon.py H | python app.py --prueba

## Vista 3D (v2)
Panel "VISTA 3D": Auto (sigue la ruta y hace zoom en los pabellones que usa) / Campus completo / un pabellon.
Slider "Ver piso 3D": 0 = todos, 1-7 = un solo piso. Cada piso tiene su color (ver leyenda).
Busqueda: escribe en Origen/Destino y elige una sugerencia (clic) o Enter para la primera.
