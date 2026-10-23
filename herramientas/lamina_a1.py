"""Pone la lámina A1 de la entrega de MIES en el cartel que cuelga en el pentágono 3D.

1. Convierte public/proyectos/mies/MIES-lamina-A1.pdf en la textura
   public/modelos/texturas/lamina-mies-a1.jpg (2048 px de alto, proporción A1).
2. Si se le pasa un .glb, cambia en él la imagen del material «lamina» (color y
   luz propia) por la nueva textura, sin tocar nada más del modelo.

Uso: python3 herramientas/lamina_a1.py [public/modelos/mies-pentagono.glb]
"""
import io
import os
import subprocess
import sys
import tempfile

import pygltflib as G
from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PDF = os.path.join(RAIZ, 'public', 'proyectos', 'mies', 'MIES-lamina-A1.pdf')
SALIDA = os.path.join(RAIZ, 'public', 'modelos', 'texturas', 'lamina-mies-a1.jpg')
ALTO = 2048


def textura():
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, 'a1')
        # 2048 px de alto en un A1 (841 mm) son unos 62 ppp: se rasteriza a más y se reduce
        subprocess.run(['pdftoppm', '-r', '150', '-png', '-singlefile', PDF, base], check=True)
        im = Image.open(base + '.png').convert('RGB')
    ancho = round(ALTO * im.width / im.height)
    im = im.resize((ancho, ALTO), Image.LANCZOS)
    im.save(SALIDA, quality=90, optimize=True)
    print(os.path.relpath(SALIDA, RAIZ), im.size, os.path.getsize(SALIDA) // 1024, 'KB')
    return SALIDA


def cambiar_en_glb(ruta, imagen):
    gl = G.GLTF2().load(ruta)
    mat = next(m for m in gl.materials if m.name == 'lamina')
    usadas = {mat.pbrMetallicRoughness.baseColorTexture.index}
    if mat.emissiveTexture:
        usadas.add(mat.emissiveTexture.index)
    fuentes = {gl.textures[t].source for t in usadas}
    nueva = open(imagen, 'rb').read()

    # se rehace el buffer copiando cada bufferView y cambiando el de la imagen
    blob = gl.binary_blob()
    cambiar = {gl.images[i].bufferView for i in fuentes}
    datos = bytearray()
    for i, bv in enumerate(gl.bufferViews):
        trozo = nueva if i in cambiar else blob[(bv.byteOffset or 0):(bv.byteOffset or 0) + bv.byteLength]
        while len(datos) % 4:
            datos += b'\0'
        bv.byteOffset = len(datos)
        bv.byteLength = len(trozo)
        datos += trozo
    while len(datos) % 4:
        datos += b'\0'
    for i in fuentes:
        gl.images[i].mimeType = 'image/jpeg'
    gl.buffers[0].byteLength = len(datos)
    gl.set_binary_blob(bytes(datos))
    gl.save_binary(ruta)
    print(os.path.basename(ruta), os.path.getsize(ruta) // 1024, 'KB')


if __name__ == '__main__':
    img = textura()
    for r in sys.argv[1:]:
        cambiar_en_glb(r, img)
