"""
Logica de la simulacion (independiente de la ventana, asi se puede probar sin pantalla).

Estados:  idle -> buscando (A* animado) -> caminando (recorrido en tiempo real) -> llego
                         +-> sin_ruta
Barrera:  mientras camina, se bloquea el siguiente tramo y se recalcula A* desde el nodo actual
          (el algoritmo se vuelve a animar).
Ascensores fuera de servicio: se pueden marcar en cualquier momento (antes de iniciar o caminando); persisten
          entre recorridos hasta reiniciar. Si la ruta actual los usa, se recalcula desde el nodo actual.
"""
import math

import algoritmos as alg
import ascensores

VEL_M_S = 1.2   # velocidad de recorrido simulada (m/s, ritmo de silla de ruedas)


class Simulador:
    def __init__(self, G):
        self.G = G
        self.solo_acc = True
        self.catalogo = ascensores.catalogo(G)
        self.asc_clave = {a["clave"]: a for a in self.catalogo}
        self.asc_de = {i: a for a in self.catalogo for i in a["nodos"]}
        self.fuera = set()
        self.sin_acceso_base = ascensores.pisos_sin_acceso(G, ())
        self.reiniciar(todo=True)

    # ------------------------------------------------------------------ estado
    def reiniciar(self, todo=False):
        if todo:
            self.origen = None
            self.destino = None
            self.fuera = set()
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
        bloq = frozenset((self.nodos_bloq | self.fuera) - {desde})
        if not alg.bfs_alcanzable(self.G, desde, self.destino, self.solo_acc, bloq, self.aristas_bloq):
            self.estado = "sin_ruta"
            self.msg = ("BFS: NO existe ruta " + ("accesible " if self.solo_acc else "") +
                        "entre esos puntos." + self._nota_fuera())
            return
        self.gen = alg.astar_pasos(self.G, desde, self.destino, self.solo_acc, bloq, self.aristas_bloq)
        self.estado = "buscando"
        self.msg = "BFS: hay conexion. Buscando la ruta optima con A*..."

    def nombres_fuera(self):
        return sorted({self.asc_de[i]["nombre"] for i in self.fuera})

    def sin_acceso_por_fuera(self):
        """Pisos que quedan sin ruta accesible SOLO por los ascensores caidos (descontando A y C, que ya no la tienen)."""
        actual = ascensores.pisos_sin_acceso(self.G, self.fuera)
        extra = {p: [x for x in pisos if x not in self.sin_acceso_base.get(p, [])] for p, pisos in actual.items()}
        return {p: v for p, v in extra.items() if v}

    def _nota_fuera(self):
        if not self.fuera:
            return ""
        extra = self.sin_acceso_por_fuera()
        resto = f" Sin acceso por eso: {ascensores.texto_pisos(extra)}." if extra else ""
        return f" Ascensores fuera de servicio: {', '.join(self.nombres_fuera())}.{resto}"

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

    def poner_ascensor(self, clave, fuera):
        """Saca de servicio (o restablece) un ascensor completo. Si la ruta que se esta recorriendo lo usa, recalcula."""
        a = self.asc_clave[clave]
        nodos = set(a["nodos"])
        if not fuera:
            self.fuera -= nodos
            self.msg = f"{a['nombre']} restablecido."
            return
        self.fuera |= nodos
        if self.estado == "buscando":
            self._buscar(self.inicio_busqueda)
            self.msg = f"{a['nombre']} fuera de servicio. " + self.msg
        elif self.estado == "caminando" and nodos & set(self.ruta[self.walker_i + 1:]):
            self.recalculos += 1
            self._buscar(self.ruta[self.walker_i])
            self.msg = f"{a['nombre']} fuera de servicio. " + self.msg
        elif self.estado == "caminando":
            self.msg = f"{a['nombre']} fuera de servicio: la ruta actual no lo usa."
        else:
            self.msg = f"{a['nombre']} fuera de servicio. Pulsa Iniciar para ver como cambia la ruta."

    def ascensor_fuera(self):
        """Saca de servicio el siguiente ascensor que la ruta aun no ha usado (todo el ascensor) y recalcula."""
        if self.estado == "buscando":
            self.msg = "A* todavia esta buscando la ruta: pulsa de nuevo cuando empiece a caminar."
            return
        if self.estado != "caminando":
            self.msg = ("Para sacar de servicio el ascensor de la ruta: pulsa Iniciar y, mientras camina, este boton. "
                        "O marca ascensores en la lista 'Ascensores fuera de servicio'.")
            return
        actual = self.asc_de.get(self.ruta[self.walker_i])
        for k in range(self.walker_i + 1, len(self.ruta)):
            a = self.asc_de.get(self.ruta[k])
            if a and a is not actual and not set(a["nodos"]) <= self.fuera:
                self.poner_ascensor(a["clave"], True)
                return
        self.msg = "La ruta actual no pasa por ningun ascensor que siga en servicio."

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
