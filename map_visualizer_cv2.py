import cv2
import numpy as np
import time
import math
import itertools
import os
import json 
class MapVisualizerCV2:
    """
    base 250 x 250 8 cuadrantes
    250/10 // 8 * 10= 30

    
    """

    def __init__(self, width=250, height=250, cuadrantes_visibles=6, distancia_max=250, max_tiempo=450, max_tiempo_conos=40, modo_estrecho=False):
        self.map_width = width
        self.map_height = height
        self.ui_line_height = 20
        self.ui_lines = 4
        self.ui_img_height = 40
        self.ui_height = self.ui_line_height * self.ui_lines + self.ui_img_height

        self.total_height = self.map_height + self.ui_height
        self.canvas = np.ones((self.total_height, self.map_width, 3), dtype=np.uint8) * 255



        if not modo_estrecho:
            cuadrantes_visibles = width // 30
        # Mapa
        self.cuad_x = 150
        self.cuad_z = 150
        self.zoom_x = self.cuad_x * (cuadrantes_visibles / 2)
        self.zoom_z = self.cuad_z * (cuadrantes_visibles / 2)

        self.pos_actual = (0, 0)
        self.tracks = []
        self.ruta = []
        self.muertes = []
        self.zonas_vacias = []

        self.modo_cuchillo = False
        self.focus = False
        self.ultima_direccion = "N/A"
        self.ultima_imagen = None  # cv2.imread('testing.png') cuando lo actualices

        self.tiempo_inicio = time.time()
        self.distancia_max = distancia_max
        self.max_tiempo = max_tiempo
        self.max_tiempo_conos = max_tiempo_conos
        self.colores_disponibles = [(255, 0, 0),(0, 255, 0),(0, 0, 255),(255, 255, 0),(0, 255, 255),(255, 0, 255),(255, 255, 255),(0, 0, 0),(128, 128, 128),(255, 165, 0),(128, 0, 128),(0, 128, 128),(128, 128, 0),(128, 0, 0),(0, 0, 128)]
        self.iterador = itertools.cycle(self.colores_disponibles)
        self.color_ruta_actual = (255, 0, 0)

        self.nombre_mapa = "mapa_5000_2.png"
        self.mapa_completo = cv2.imread(rf"G:\ExtensionChrome\RUSTAUTO\butcher\{self.nombre_mapa}")
        self.map_size  = 5000  # metros
        self.mapa_resolucion = 1440  # pixeles
        self.escala_mapa = self.mapa_resolucion / self.map_size   # pixeles por metro

        self.min_x = -self.map_size / 2
        self.max_x = self.map_size / 2
        self.min_z = -self.map_size / 2
        self.max_z = self.map_size / 2


    def renderizar_mapa_fondo(self):
        if self.mapa_completo is None:
            return

        cx, cz = self.pos_actual
        half_x = self.zoom_x
        half_z = self.zoom_z

        # Escala de conversión
        scale_x = self.escala_mapa
        scale_z = self.escala_mapa

        # Centro del jugador en la imagen
        centro_img_x = int((cx - self.min_x) * scale_x)
        centro_img_z = int((self.max_z - cz) * scale_z)

        # Tamaño del área a recortar (en pixeles)
        render_px_w = self.map_width
        render_px_h = self.map_height

        # Coordenadas del recorte en la imagen del mapa
        src_x1 = centro_img_x - render_px_w // 2
        src_x2 = centro_img_x + render_px_w // 2
        src_z1 = centro_img_z - render_px_h // 2
        src_z2 = centro_img_z + render_px_h // 2

        # Clipping si se sale fuera de la imagen
        src_x1_clip = max(src_x1, 0)
        src_z1_clip = max(src_z1, 0)
        src_x2_clip = min(src_x2, self.mapa_completo.shape[1])
        src_z2_clip = min(src_z2, self.mapa_completo.shape[0])

        # Dimensiones efectivas del recorte
        cropped_w = src_x2_clip - src_x1_clip
        cropped_h = src_z2_clip - src_z1_clip

        # Coordenadas en el canvas (centrado)
        dst_x1 = (self.map_width - cropped_w) // 2
        dst_x2 = dst_x1 + cropped_w
        dst_z1 = (self.map_height - cropped_h) // 2
        dst_z2 = dst_z1 + cropped_h

        # Solo renderizar si hay algo visible
        if cropped_w > 0 and cropped_h > 0:
            self.canvas[dst_z1:dst_z2, dst_x1:dst_x2] = self.mapa_completo[src_z1_clip:src_z2_clip, src_x1_clip:src_x2_clip]

    def cambiar_color_ruta(self):
        self.color_ruta_actual = next(self.iterador)

    def guardar_muerte_persistente(self, pos):
        archivo = "muertes_animales.json"
        mapa_key = os.path.basename(self.nombre_mapa)  # o self.nombre_mapa si lo tienes


        if os.path.exists(archivo):
            with open(archivo, "r") as f:
                data = json.load(f)
        else:
            data = {}

        if mapa_key not in data:
            data[mapa_key] = []



        data[mapa_key].append({
            "x": pos[0],
            "z": pos[1],
            "timestamp": time.time()
        })

        with open(archivo, "w") as f:
            json.dump(data, f, indent=2)

    def world_to_screen(self, x, z):
        cx, cz = self.pos_actual
        scale_x = self.map_width / (2 * self.zoom_x)
        scale_z = self.map_height / (2 * self.zoom_z)
        sx = int(self.map_width / 2 + (x - cx) * scale_x)
        sy = int(self.map_height / 2 - (z - cz) * scale_z)
        return sx, sy
    def world_radius_to_screen(self, r):
        scale = self.map_width / (2 * self.zoom_x)
        return int(r * scale)
    
    def actualizar_posicion(self, pos):
        ahora = time.time()
        self.pos_actual = pos
        self.ruta.append((pos, ahora, self.color_ruta_actual))

    def registrar_zona_vacia(self):
        self.zonas_vacias.append((self.pos_actual, time.time()))

    def agregar_track(self, angulo_deg):
        self.tracks.append((self.pos_actual, angulo_deg, time.time()))

    def registrar_muerte(self):
        print(f"ANIMAL MUERTO EN {self.pos_actual}")
        self.muertes.append((self.pos_actual, time.time()))
        self.guardar_muerte_persistente(self.pos_actual)

    def dibujar_cono(self, x, z, angulo_deg, color=(0, 0, 153), alpha=0.4):
        angulo_rad = math.radians(angulo_deg)
        spread = math.radians(15)
        dx1 = self.distancia_max * math.cos(angulo_rad - spread)
        dz1 = self.distancia_max * math.sin(angulo_rad - spread)
        dx2 = self.distancia_max * math.cos(angulo_rad + spread)
        dz2 = self.distancia_max * math.sin(angulo_rad + spread)

        p0 = self.world_to_screen(x, z)
        p1 = self.world_to_screen(x + dx1, z + dz1)
        p2 = self.world_to_screen(x + dx2, z + dz2)

        pts = np.array([p0, p1, p2], np.int32)

        overlay = self.canvas.copy()
        cv2.fillPoly(overlay, [pts], color)
        cv2.addWeighted(overlay, alpha, self.canvas, 1 - alpha, 0, self.canvas)

    def dibujar_zona_vacia(self, x, z, color=(150, 150, 150), alpha=0.25):
        px, py = self.world_to_screen(x, z)
        radio_px = self.world_radius_to_screen(self.distancia_max)

        overlay = self.canvas.copy()
        cv2.circle(overlay, (px, py), radio_px, color, -1)
        cv2.addWeighted(overlay, alpha, self.canvas, 1 - alpha, 0, self.canvas)

    def notificar_tp(self):
        self.color_ruta_actual = (0, 0, 255)

    def limpiar_viejos(self):
        ahora = time.time()
        self.tracks = [t for t in self.tracks if ahora - t[2] <= self.max_tiempo_conos]
        self.muertes = [m for m in self.muertes if ahora - m[1] <= self.max_tiempo]
        self.ruta = [r for r in self.ruta if ahora - r[1] <= self.max_tiempo]
        self.zonas_vacias = [z for z in self.zonas_vacias if ahora - z[1] <= self.max_tiempo]

    def set_modo_cuchillo_estado(self, estado):
        self.modo_cuchillo = estado

    def actualizar_interfaz(self):
        y_offset = self.map_height
        info = [
            f"Pos: {self.pos_actual[0]:.1f}, {self.pos_actual[1]:.1f}",
            f"Modo cuchillo: {self.modo_cuchillo}",
            f"Focus: {'Si' if self.focus else 'No'}",
            f"Ultima direccion: {self.ultima_direccion}"
        ]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        color = (0, 0, 0)

        for line in info:
            cv2.putText(self.canvas, line, (5, y_offset + 14), font, font_scale, color, 1, cv2.LINE_AA)
            y_offset += self.ui_line_height

        # Mostrar imagen si existe
        if self.ultima_imagen is not None:
            h_img = self.ui_img_height
            img_resized = cv2.resize(self.ultima_imagen, (self.map_width, h_img))
            self.canvas[self.total_height - h_img:self.total_height, 0:self.map_width] = img_resized

    def actualizar(self):
        # Limpia toda el área (mapa + interfaz)
        self.canvas[:, :] = 255

        # Pega el fondo del mapa solo en el área del mapa (evita la interfaz)
        self.renderizar_mapa_fondo()

        self.limpiar_viejos()

        # Rutas
        for i in range(1, len(self.ruta)):
            p1 = self.world_to_screen(*self.ruta[i - 1][0])
            p2 = self.world_to_screen(*self.ruta[i][0])
            color = self.ruta[i][2]
            cv2.line(self.canvas, p1, p2, color, 2)

        # Conos
        for pos, angulo, _ in self.tracks:
            self.dibujar_cono(pos[0], pos[1], angulo)

        # Muertes
        for pos, _ in self.muertes:
            px, py = self.world_to_screen(*pos)
            cv2.drawMarker(self.canvas, (px, py), (0, 0, 255), cv2.MARKER_TILTED_CROSS, 10, 2)

        # Zonas vacías
        for pos, _ in self.zonas_vacias:
            self.dibujar_zona_vacia(pos[0], pos[1])

        # Jugador actual
        px, py = self.world_to_screen(*self.pos_actual)
        cv2.circle(self.canvas, (px, py), 4, (0, 255, 0), -1)

        # Renderizar UI debajo
        self.actualizar_interfaz()

        # Mostrar
        cv2.imshow("Rust Map", self.canvas)
        cv2.waitKey(1)



""""
import cv2
import numpy as np
import time
import math

class MapVisualizerCV2:
    def __init__(self, width=320, height=320, cuadrantes_visibles=5, distancia_max=250, max_tiempo=300):
        self.width = width
        self.height = height
        self.panel_altura = 40
        self.canvas = np.ones((height + self.panel_altura, width, 3), dtype=np.uint8) * 255

        self.cuad_x = 150
        self.cuad_z = 150
        self.zoom_x = self.cuad_x * (cuadrantes_visibles / 2)
        self.zoom_z = self.cuad_z * (cuadrantes_visibles / 2)

        self.pos_actual = (0, 0)
        self.ruta = []
        self.tracks = []
        self.muertes = []
        self.zonas_vacias = []

        self.tiempo_inicio = time.time()
        self.distancia_max = distancia_max
        self.max_tiempo = max_tiempo
        self.color_ruta_actual = (255, 0, 0)

        


    def world_to_screen(self, x, z):
        cx, cz = self.pos_actual
        scale_x = self.width / (2 * self.zoom_x)
        scale_z = self.height / (2 * self.zoom_z)
        sx = int(self.width / 2 + (x - cx) * scale_x)
        sy = int(self.height / 2 - (z - cz) * scale_z)
        return sx, sy

    def world_radius_to_screen(self, r):
        scale = self.width / (2 * self.zoom_x)
        return int(r * scale)

    def actualizar_posicion(self, pos):
        ahora = time.time()
        self.pos_actual = pos
        self.ruta.append((pos, ahora, self.color_ruta_actual))

    def agregar_track(self, angulo_deg):
        self.tracks.append((self.pos_actual, angulo_deg, time.time()))

    def registrar_muerte(self):
        self.muertes.append((self.pos_actual, time.time()))

    def registrar_zona_vacia(self):
        self.zonas_vacias.append((self.pos_actual, time.time()))

    def notificar_tp(self):
        self.color_ruta_actual = (0, 0, 255)

    def limpiar_viejos(self):
        ahora = time.time()
        self.ruta = [r for r in self.ruta if ahora - r[1] <= self.max_tiempo]
        self.tracks = [t for t in self.tracks if ahora - t[2] <= self.max_tiempo]
        self.muertes = [m for m in self.muertes if ahora - m[1] <= self.max_tiempo]
        self.zonas_vacias = [z for z in self.zonas_vacias if ahora - z[1] <= self.max_tiempo]

    def dibujar_cono(self, x, z, angulo_deg, color=(0, 0, 153), alpha=0.4):
        angulo_rad = math.radians(angulo_deg)
        spread = math.radians(15)
        dx1 = self.distancia_max * math.cos(angulo_rad - spread)
        dz1 = self.distancia_max * math.sin(angulo_rad - spread)
        dx2 = self.distancia_max * math.cos(angulo_rad + spread)
        dz2 = self.distancia_max * math.sin(angulo_rad + spread)

        p0 = self.world_to_screen(x, z)
        p1 = self.world_to_screen(x + dx1, z + dz1)
        p2 = self.world_to_screen(x + dx2, z + dz2)

        pts = np.array([p0, p1, p2], np.int32)

        overlay = self.canvas.copy()
        cv2.fillPoly(overlay, [pts], color)
        cv2.addWeighted(overlay, alpha, self.canvas, 1 - alpha, 0, self.canvas)

    def dibujar_zona_vacia(self, x, z, color=(150, 150, 150), alpha=0.25):
        px, py = self.world_to_screen(x, z)
        radio_px = self.world_radius_to_screen(self.distancia_max)

        overlay = self.canvas.copy()
        cv2.circle(overlay, (px, py), radio_px, color, -1)
        cv2.addWeighted(overlay, alpha, self.canvas, 1 - alpha, 0, self.canvas)

    def actualizar(self):
        self.canvas[:] = 255
        self.limpiar_viejos()

        for i in range(1, len(self.ruta)):
            p1 = self.world_to_screen(*self.ruta[i - 1][0])
            p2 = self.world_to_screen(*self.ruta[i][0])
            color = self.ruta[i][2]
            cv2.line(self.canvas, p1, p2, color, 2)

        for pos, angulo, _ in self.tracks:
            self.dibujar_cono(pos[0], pos[1], angulo)

        for pos, _ in self.zonas_vacias:
            self.dibujar_zona_vacia(pos[0], pos[1])

        for pos, _ in self.muertes:
            px, py = self.world_to_screen(*pos)
            cv2.drawMarker(self.canvas, (px, py), (0, 0, 255), cv2.MARKER_TILTED_CROSS, 20, 2)

        px, py = self.world_to_screen(*self.pos_actual)
        cv2.circle(self.canvas, (px, py), 4, (0, 255, 0), -1)

        cv2.imshow("Rust Map", self.canvas)
        cv2.waitKey(1)
"""