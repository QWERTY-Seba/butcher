import time
import pyautogui
import win32gui
import cv2
import keyboard  # pip install keyboard
from map_visualizer_cv2 import MapVisualizerCV2
from extraer_texto import extraer_direccion_track  
from modo_cuchillo import ModoCuchilloHandler
import pyperclip
import re
import os

def rust_tiene_focus(nombre_ventana='Rust'):
    hwnd = win32gui.GetForegroundWindow()
    titulo = win32gui.GetWindowText(hwnd)
    return nombre_ventana == titulo

def obtener_hwnd_rust(nombre_ventana='Rust'):
    def enum_callback(hwnd, resultado):
        if nombre_ventana == win32gui.GetWindowText(hwnd):
            resultado.append(hwnd)
    resultado = []
    win32gui.EnumWindows(enum_callback, resultado)
    return resultado[0] if resultado else None

DIRECCIONES_ANGULO = {
    #CAMBIAR ESTOS VALORES ESTAN MAL PERO FUNCIONAN TAMBIEN CAMBIAR LA FORMULA PARA QUE ESTO TENGA SENTIDO
    "East": 0,
    "North-East": 45,
    "North": 90,
    "North-West": 135,
    "West": 180,
    "South-West": 225,
    "South": 270,
    "South-East": 315,
}
def leer_posicion_portapapeles():
    texto = pyperclip.paste()
    m = re.search(r'\((-?\d+\.\d+),\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\)', texto)
    if not m:
        return None
    x = float(m.group(1))
    z = float(m.group(3))
    return (x, z)






def main_loop():
    pyautogui.FAILSAFE = False
    ancho_ventanilla = 350
    
    mapa = MapVisualizerCV2(ancho_ventanilla,350)

    hwnd_rust = obtener_hwnd_rust()
    if hwnd_rust is None:
        print("No se encontró la ventana de Rust")  # Único print permitido
        return

    def on_c_pressed():
        if not rust_tiene_focus():
            return

        time.sleep(0.5)
        tipo, direccion_larga = extraer_direccion_track(hwnd_rust)

        # Guardar imagen testing.png como última usada
        if os.path.exists("testing.png"):
            mapa.ultima_imagen = cv2.imread("testing.png")

        if tipo == "track" and direccion_larga in DIRECCIONES_ANGULO:
            angulo = DIRECCIONES_ANGULO[direccion_larga]
            mapa.agregar_track(angulo)
            mapa.ultima_direccion = f"{direccion_larga} {angulo}"
        elif tipo == "vacio":
            mapa.registrar_zona_vacia()
            mapa.ultima_direccion = "Zona sin animales"
        else:
            mapa.ultima_direccion = "No se pudo detectar direccion"

   

    cv2.namedWindow("Rust Map", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Rust Map", ancho_ventanilla, ancho_ventanilla+120)
    cv2.setWindowProperty("Rust Map", cv2.WND_PROP_TOPMOST, 1)

    # Estado inicial
    mapa.ultima_direccion = "Esperando entrada"
    mapa.ultima_imagen = None
    mapa.modo_cuchillo = False
    modo_cuchillo = ModoCuchilloHandler(on_estado_cambiado=mapa.set_modo_cuchillo_estado, on_confirmado= mapa.registrar_muerte)


    def on_key_event(event):
        if not event.event_type == 'down':
            return
        
        if event.name.lower() == 'c':
            on_c_pressed()
        
        if event.name.lower() == '3':
            modo_cuchillo.activar()

        if (event.name.lower() == 'f2' or event.name.lower() == 'f3' or event.name.lower() == 'f4'):
            mapa.cambiar_color_ruta()

    
    keyboard.hook(on_key_event)
    try:
        while True:
            mapa.focus = rust_tiene_focus()

            if mapa.focus:
                pyautogui.press('scrolllock')
                time.sleep(0.15)
                pos = leer_posicion_portapapeles()
                if pos:
                    mapa.actualizar_posicion(pos)
                    mapa.pos_actual_valida = True
                else:
                    mapa.pos_actual_valida = False
            else:
                mapa.pos_actual_valida = False

            mapa.actualizar()

            if cv2.waitKey(1) == 27:  # ESC
                break

    except KeyboardInterrupt:
        print("Salida manual.")
    finally:
        cv2.destroyAllWindows()

main_loop()