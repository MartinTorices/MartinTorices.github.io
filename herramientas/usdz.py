"""Genera los .usdz para la realidad aumentada del iPhone (AR Quick Look).

model-viewer puede crearlos al pulsar el botón, pero es lento y en algunas
versiones de iOS falla; con el archivo ya hecho (atributo ios-src) va a la primera.
Usa el mismo exportador de three.js que model-viewer, en un Chromium sin ventana.

Uso: python3 herramientas/usdz.py public/modelos/mies-inferior.glb [...]
     (deja cada .usdz junto a su .glb; necesita npm install y Playwright)
"""
import base64
import functools
import http.server
import io
import os
import struct
import sys
import threading
import zipfile

from PIL import Image

from playwright.sync_api import sync_playwright

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def aligerar(datos, calidad=85):
    """Pasa las texturas PNG del exportador a JPEG (la veta y el cepillado apenas
    comprimen en PNG) y vuelve a empaquetar el USDZ como pide Apple: sin compresión
    y con los datos de cada archivo alineados a 64 bytes."""
    origen = zipfile.ZipFile(io.BytesIO(datos))
    archivos = {}
    cambios = {}
    for info in origen.infolist():
        contenido = origen.read(info.filename)
        if info.filename.endswith('.png'):
            im = Image.open(io.BytesIO(contenido))
            if im.mode in ('RGBA', 'LA') and im.getchannel('A').getextrema()[0] < 255:
                archivos[info.filename] = contenido          # con transparencia: se queda en PNG
                continue
            buf = io.BytesIO()
            im.convert('RGB').save(buf, 'JPEG', quality=calidad, optimize=True)
            nuevo = info.filename[:-4] + '.jpg'
            cambios[info.filename] = nuevo
            archivos[nuevo] = buf.getvalue()
        else:
            archivos[info.filename] = contenido
    for nombre in list(archivos):
        if nombre.endswith('.usda'):
            texto = archivos[nombre].decode('utf-8')
            for viejo, nuevo in cambios.items():
                texto = texto.replace(viejo, nuevo)
            archivos[nombre] = texto.encode('utf-8')
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, 'w', zipfile.ZIP_STORED) as z:
        for nombre, contenido in archivos.items():      # model.usda va primero
            info = zipfile.ZipInfo(nombre, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            inicio = salida.tell() + 30 + len(nombre.encode())
            relleno = (64 - inicio % 64) % 64
            if 0 < relleno < 4:
                relleno += 64
            if relleno:
                info.extra = struct.pack('<HH', 0x1986, relleno - 4) + b'\0' * (relleno - 4)
            z.writestr(info, contenido)
    return salida.getvalue()


def main(glbs):
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=RAIZ)
    manejador.log_message = lambda *a: None
    servidor = http.server.ThreadingHTTPServer(('127.0.0.1', 0), manejador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{servidor.server_port}'
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pagina = nav.new_page()
        pagina.on('console', lambda m: None)
        pagina.goto(f'{base}/herramientas/usdz.html')
        pagina.wait_for_function('window.listo === true')
        for glb in glbs:
            ruta = os.path.relpath(os.path.abspath(glb), RAIZ).replace(os.sep, '/')
            datos = aligerar(base64.b64decode(pagina.evaluate('u => convertir(u)', f'/{ruta}')))
            salida = os.path.splitext(os.path.abspath(glb))[0] + '.usdz'
            open(salida, 'wb').write(datos)
            print(os.path.basename(salida), len(datos) // 1024, 'KB')
        nav.close()
    servidor.shutdown()


if __name__ == '__main__':
    main(sys.argv[1:])
