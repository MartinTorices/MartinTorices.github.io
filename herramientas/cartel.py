"""Convierte herramientas/cartel-mies.html en la imagen del cartel A1 del modelo 3D.

Uso: python3 herramientas/cartel.py   (deja public/modelos/texturas/cartel-mies.jpg)
Después: python3 herramientas/mies_modelos_pbr.py <carpeta glb> y herramientas/glb_autonomo.py
"""
import functools
import http.server
import os
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SALIDA = os.path.join(RAIZ, 'public', 'modelos', 'texturas', 'cartel-mies.jpg')

manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=RAIZ)
manejador.log_message = lambda *a: None
servidor = http.server.ThreadingHTTPServer(('127.0.0.1', 0), manejador)
threading.Thread(target=servidor.serve_forever, daemon=True).start()
with sync_playwright() as p:
    nav = p.chromium.launch()
    pg = nav.new_page(viewport={'width': 1446, 'height': 2048})
    pg.goto(f'http://127.0.0.1:{servidor.server_port}/herramientas/cartel-mies.html')
    pg.wait_for_load_state('networkidle')
    pg.evaluate('document.fonts.ready')
    png = SALIDA[:-4] + '.png'
    pg.screenshot(path=png)
    nav.close()
servidor.shutdown()
Image.open(png).convert('RGB').save(SALIDA, quality=90, optimize=True)
os.remove(png)
print(SALIDA, Image.open(SALIDA).size)
