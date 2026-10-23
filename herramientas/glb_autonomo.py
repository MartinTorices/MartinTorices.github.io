"""Mete dentro del .glb las texturas que estaban como archivos aparte.

Las texturas compartidas (public/modelos/texturas/) se descargan una sola vez en la
web, pero la realidad aumentada de Android (Scene Viewer, la app de Google) no
siempre carga archivos externos: se queda «pillada» y vuelve a la página. Con todo
dentro del .glb funciona siempre. Las texturas se reducen a 1024 px como mucho (la lámina A1, a 2048).

Uso: python3 herramientas/glb_autonomo.py public/modelos/x.glb [...]
"""
import io
import os
import sys

import pygltflib as G
from PIL import Image


def autonomo(ruta, max_lado=1024, calidad=85):
    gl = G.GLTF2().load(ruta)
    base = os.path.dirname(os.path.abspath(ruta))
    datos = bytearray(gl.binary_blob() or b'')
    for img in gl.images:
        if not img.uri:
            continue
        im = Image.open(os.path.join(base, img.uri)).convert('RGB')
        # la lámina A1 conserva 2048 px para que se lea; el resto, max_lado
        lado = 2048 if 'lamina' in img.uri else max_lado
        im.thumbnail((lado, lado), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=calidad, optimize=True)
        b = buf.getvalue()
        while len(datos) % 4:
            datos += b'\0'
        gl.bufferViews.append(G.BufferView(buffer=0, byteOffset=len(datos), byteLength=len(b)))
        datos += b
        img.bufferView = len(gl.bufferViews) - 1
        img.mimeType = 'image/jpeg'
        img.uri = None
    while len(datos) % 4:
        datos += b'\0'
    gl.buffers[0].byteLength = len(datos)
    gl.set_binary_blob(bytes(datos))
    gl.save_binary(ruta)
    print(os.path.basename(ruta), os.path.getsize(ruta) // 1024, 'KB')


if __name__ == '__main__':
    for r in sys.argv[1:]:
        autonomo(r)
