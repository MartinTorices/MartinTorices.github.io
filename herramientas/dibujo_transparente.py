"""Quita el papel blanco de un dibujo (planos, alzados, esquemas) dejándolo transparente.

Los archivos «-dibujo» se muestran sobre una hoja clara: si el papel blanco se queda,
salen recuadros blancos (huecos cerrados que un recorte por contorno no alcanza,
agujeros de los perfiles…). Aquí se vuelve transparente TODO el blanco neutro, con una
rampa suave y quitando el blanco mezclado en los bordes de las líneas.

Uso: python3 herramientas/dibujo_transparente.py entrada.jpg salida-dibujo.png [px_a_quitar_derecha]
"""
import sys
import numpy as np
from PIL import Image


def dibujo(entrada, salida, recorte_derecho=0, margen=12):
    im = np.array(Image.open(entrada).convert('RGB')).astype(np.float32)
    if recorte_derecho:
        im = im[:, : im.shape[1] - recorte_derecho]
    mn = im.min(2)
    croma = im.max(2) - mn
    blancura = np.clip((mn - 222) / 20, 0, 1) * np.clip((14 - croma) / 8, 0, 1)
    alfa = 1 - blancura
    a = np.maximum(alfa, 1e-3)[..., None]
    limpio = np.clip(255 + (im - 255) / a, 0, 255)       # color sin el blanco mezclado
    limpio = np.where(alfa[..., None] > 0.98, im, limpio)
    out = Image.fromarray(np.dstack([limpio, alfa * 255]).astype(np.uint8), 'RGBA')
    ys, xs = np.where(alfa > 0.3)
    out = out.crop((max(xs.min() - margen, 0), max(ys.min() - margen, 0),
                    min(xs.max() + margen, im.shape[1]), min(ys.max() + margen, im.shape[0])))
    out.save(salida, optimize=True)


if __name__ == '__main__':
    dibujo(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
