import numpy as np
import cv2
import pytesseract
import win32gui
import win32ui
from ctypes import windll

# Puedes cambiar esto si lo tienes en otra ruta
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DIRECCIONES_VALIDAS = [
    "North-East", "South-West", "North-West",  "South-East",
    "North","South","West","East"
]

import cv2
import numpy as np
import pytesseract

def extraer_texto_blanco_negro(img):
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    cv2.imwrite("gray_testing.png", gray)
    # Crear una máscara para letras blancas
    mask_blanco = cv2.inRange(gray, 210, 255)

    inverted = cv2.bitwise_not(mask_blanco)

    h, w = inverted.shape
    mask_ff = inverted.copy()
    flood_mask = np.zeros((h+2, w+2), np.uint8)  # +2 por requerimiento de floodFill

    # Flood fill desde todos los bordes (arriba, abajo, izq, der)
    for x in range(w):
        cv2.floodFill(mask_ff, flood_mask, (x, 0), 255)      # borde sup
        cv2.floodFill(mask_ff, flood_mask, (x, h-1), 255)    # borde inf
    for y in range(h):
        cv2.floodFill(mask_ff, flood_mask, (0, y), 255)      # borde izq
        cv2.floodFill(mask_ff, flood_mask, (w-1, y), 255)  


    #letras = cv2.bitwise_not(mask_ff)
    letras = cv2.resize(mask_ff, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Mostrar para debug
    cv2.imwrite("Testing.png", letras)

    # OCR con configuración ajustada
    config = '--psm 6'  # Una línea de texto
    texto = pytesseract.image_to_string(letras, config=config, lang='eng')

    return texto.strip()



def extraer_direccion_track(hwnd):
    # Obtener captura completa de la ventana Rust
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bot - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)

    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    # Cortar la zona donde aparece el mensaje (relativo)

    #CAMBIAR ESTE SISTEMA A ALGO MAS DECENTE
    x0 = int(width * 0.02)
    x1 = int(width * 0.18)
    y0 = int(height * 0.845)
    y1 = int(height * 0.865)

    img_crop = img[y0:y1, x0:x1]

    texto = extraer_texto_blanco_negro(img_crop)
    print(texto)

    for direccion in sorted(DIRECCIONES_VALIDAS, key=len, reverse=True):
        if direccion in texto:
            return ("track", direccion)

    if "No animals were found" in texto:
        return ("vacio", None)
    
    return (None, None)
