import time
import threading
import keyboard
import mouse

class ModoCuchilloHandler:
    def __init__(self, on_estado_cambiado, on_confirmado, tiempo_espera=10, tiempo_mantener=5):
        self.estado = "inactivo"
        self.on_estado_cambiado = on_estado_cambiado
        self.on_confirmado = on_confirmado
        self.tiempo_espera = tiempo_espera
        self.tiempo_mantener = tiempo_mantener
        self._inicio_espera = None
        self._inicio_mantener = None
        self._lock = threading.Lock()

        # Iniciar monitoreo
        threading.Thread(target=self._monitorear_estado, daemon=True).start()
        mouse.on_button(self._on_click, buttons=mouse.LEFT, types=mouse.DOWN)
        mouse.on_button(self._on_release, buttons=mouse.LEFT, types=mouse.UP)

        # Escucha tecla 'k'
        keyboard.add_hotkey('k', self.activar)

    def activar(self):
        with self._lock:
            if self.estado == "inactivo":
                self.estado = "esperando click"
                self._inicio_espera = time.time()
                self._inicio_mantener = None
                self._notificar()

    def _notificar(self):
        self.on_estado_cambiado(self.estado)

    def _on_click(self):
        with self._lock:
            if self.estado == "esperando click":
                self.estado = "manteniendo click"
                self._inicio_mantener = time.time()
                self._notificar()

    def _on_release(self):
        with self._lock:
            if self.estado == "manteniendo click":
                duracion = time.time() - self._inicio_mantener
                if duracion >= self.tiempo_mantener:
                    self.estado = "inactivo"
                    self._notificar()
                    self.on_confirmado()
                else:
                    self.estado = "inactivo"
                    self._notificar()

    def _monitorear_estado(self):
        while True:
            time.sleep(0.1)
            with self._lock:
                if self.estado == "esperando click" and (time.time() - self._inicio_espera) > self.tiempo_espera:
                    self.estado = "inactivo"
                    self._notificar()
