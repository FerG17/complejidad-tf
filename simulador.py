"""
Logica de la simulacion (independiente de la ventana, asi se puede probar sin pantalla).

Estados:  idle -> buscando (A* animado) -> caminando (recorrido en tiempo real) -> llego
                         +-> sin_ruta
Barrera:  mientras camina, se bloquea el siguiente tramo (o el siguiente ascensor) y se
          recalcula A* desde el nodo actual (el algoritmo se vuelve a animar).
"""
import math

import algoritmos as alg

VEL_M_S = 1.2   # velocidad de recorrido simulada (m/s, ritmo de silla de ruedas)


class Simulador:
    def __init__(self, G):
        self.G = G
        self.solo_acc = True
        self.reiniciar(todo=True)

    # ------------------------------------------------------------------ estado
    def reiniciar(self, todo=False):
        if todo:
            self.origen = None
            self.destino = None
        self.estado = "idle"
        self.gen = None
        self.expandidos = []
        self.n_exp = 0
        self.ruta = None
        self.costo = 0.0
        self.aristas_bloq = set()
        self.nodos_bloq = set()
        self.recalculos = 0
        self.walker_i = 0          # indice del ultimo nodo de la ruta alcanzado
        self.walker_s = 0.0        # metros recorridos dentro del tramo actual
        self.recorrido = []        # nodos ya recorridos (para pintar el rastro)
        self.msg = "Elige origen y destino en el plano (clic izq = origen, clic der = destino)."
        self.inicio_busqueda = None

    def iniciar(self):
        if not self.origen or not self.destino:
            self.msg = "Falta elegir origen y/o destino."
            return
        if self.origen == self.destino:
            self.msg = "Origen y destino son el mismo punto."
            return
        self.aristas_bloq.clear()
        self.nodos_bloq.clear()
        self.recalculos = 0
        self.recorrido = [self.origen]
        self._buscar(self.origen)

    def _buscar(self, desde):
        self.inicio_busqueda = desde
        self.expandidos = []
        self.n_exp = 0
        self.ruta = None
        if not alg.bfs_alcanzable(self.G, desde, self.destino, self.solo_acc, self.nodos_bloq, self.aristas_bloq):
            self.estado = "sin_ruta"
            self.msg = ("BFS: NO existe ruta " + ("accesible " if self.solo_acc else "") +
                        "entre esos puntos.")
            return
        self.gen = alg.astar_pasos(self.G, desde, self.destino, self.solo_acc, self.nodos_bloq, self.aristas_bloq)
        self.estado = "buscando"
        self.msg = "BFS: hay conexion. Buscando la ruta optima con A*..."

    # ------------------------------------------------------------------ tick
    def tick(self, pasos_busqueda=6, dt=0.04, mult=6.0):
        """Avanza la simulacion un poco. Devuelve True si algo cambio."""
        if self.estado == "buscando":
            for _ in range(pasos_busqueda):
                ev = next(self.gen)
                if ev[0] == "expand":
                    self.expandidos.append(ev[1])
                    self.n_exp = ev[3]
                elif ev[0] == "fin":
                    self.ruta, self.costo = ev[1], ev[2]
                    self.walker_i, self.walker_s = 0, 0.0
                    self.estado = "caminando"
                    self.msg = (f"Ruta encontrada: {len(self.ruta)} nodos, costo {self.costo:.0f} m-eq, "
                                f"{self.n_exp} nodos expandidos. Recorriendo...")
                    break
                else:
                    self.estado = "sin_ruta"
                    self.msg = "A*: sin ruta."
                    break
            return True
        if self.estado == "caminando":
            avance = VEL_M_S * dt * mult
            while avance > 0 and self.walker_i < len(self.ruta) - 1:
                a, b = self.ruta[self.walker_i], self.ruta[self.walker_i + 1]
                largo = max(self.G.d3(a, b), 0.01)
                falta = largo - self.walker_s
                if avance >= falta:
                    avance -= falta
                    self.walker_i += 1
                    self.walker_s = 0.0
                    self.recorrido.append(self.ruta[self.walker_i])
                else:
                    self.walker_s += avance
                    avance = 0
            if self.walker_i >= len(self.ruta) - 1:
                self.estado = "llego"
                self.msg = f"Llegaste a destino. Recalculos por barreras: {self.recalculos}."
            return True
        return False

    # ------------------------------------------------------------------ barreras
    def barrera_tramo(self):
        """Bloquea el siguiente tramo de la ruta y recalcula desde el nodo actual."""
        if self.estado != "caminando" or self.walker_i >= len(self.ruta) - 1:
            return
        a, b = self.ruta[self.walker_i], self.ruta[self.walker_i + 1]
        self.aristas_bloq.add((a, b))
        self.recalculos += 1
        self._buscar(a)
        if self.estado == "sin_ruta":
            self.msg += " (la barrera dejo el destino aislado)"

    def ascensor_fuera(self):
        """Pone fuera de servicio el siguiente ascensor de la ruta (si lo hay) y recalcula."""
        if self.estado != "caminando":
            return
        for k in range(self.walker_i + 1, len(self.ruta)):
            if self.G.nodos[self.ruta[k]]["tipo"] == "ascensor":
                self.nodos_bloq.add(self.ruta[k])
                self.recalculos += 1
                self._buscar(self.ruta[self.walker_i])
                self.msg = "Ascensor fuera de servicio. " + self.msg
                return
        self.msg = "La ruta actual no usa ascensores."

    # ------------------------------------------------------------------ posicion
    def pos_walker(self):
        """(x_px, y_px, x_m, y_m, z_m) del caminante, interpolado sobre el tramo actual."""
        if not self.ruta:
            return None
        i = self.walker_i
        A = self.G.nodos[self.ruta[i]]
        if i >= len(self.ruta) - 1:
            return A["x_px"], A["y_px"], A["x"], A["y"], A["z"]
        B = self.G.nodos[self.ruta[i + 1]]
        t = min(self.walker_s / max(self.G.d3(A["id"], B["id"]), 0.01), 1.0)
        return tuple(A[k] + (B[k] - A[k]) * t for k in ("x_px", "y_px", "x", "y", "z"))

    def distancia_recorrida(self):
        s = 0.0
        for a, b in zip(self.recorrido, self.recorrido[1:]):
            s += self.G.d3(a, b)
        return s
