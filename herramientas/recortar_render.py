"""Quita el fondo blanco (y sus sombras grises) de un render, con bordes limpios.

Pensado para renders de CAD con fondo blanco liso y sombras suaves, en los que la
pieza tiene madera clara (que el recorte automático confunde con el fondo):
  1. Fondo = píxeles grises neutros (sin color) y con poco gradiente, conectados con
     el borde de la imagen; también las zonas cerradas claras (fondo y sombras que se
     ven entre perfiles y baldas) y las perforaciones de los perfiles. La madera tiene
     color, así que no entra; las caras de los perfiles son grises oscuras y se quedan.
  2. Los brillos blancos dentro de la madera no son fondo: se quedan, pero se
     suavizan hacia el color de la madera de alrededor (sobre el fondo oscuro de la
     web parecían manchas de fondo mal quitado).
  3. Borde de 2 px con transparencia gradual y sin el halo blanco del fondo.
  4. Recorte al contenido, margen y, si se pide, lienzo con una proporción fija.

Uso: python3 herramientas/recortar_render.py entrada.jpg salida.png [aspecto] [--sin-brillos]
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def alargamiento(m):
    """Relación entre el eje largo y el corto de una zona (1 = redonda)."""
    ys, xs = np.nonzero(m)
    ev = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([xs, ys]))))
    return float(np.sqrt(ev[1] / max(ev[0], 1e-6)))


def recortar(entrada, salida, aspecto=None, suavizar_brillos=True, max_lado=2000):
    im = np.array(Image.open(entrada).convert('RGB')).astype(np.float32)
    h, w, _ = im.shape
    L = im.mean(2)
    croma = im.max(2) - im.min(2)
    media = ndi.uniform_filter(L, 5)
    sd = np.sqrt(np.maximum(ndi.uniform_filter(L * L, 5) - media * media, 0))

    # 1. candidatos a fondo: neutros (sin color) y con poco cambio de un píxel a otro.
    #    El contorno de los perfiles y las baldas tiene mucho gradiente y hace de muro.
    Ls = ndi.gaussian_filter(L, 1.0)
    grad = np.hypot(ndi.sobel(Ls, 0), ndi.sobel(Ls, 1)) / 8
    candidato = (croma < 10) & (grad < 3) & (L > 95)
    lab, n = ndi.label(candidato)
    borde = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    fondo = np.isin(lab, borde[borde > 0])
    # zonas cerradas: es fondo si es clara (los perfiles son grises oscuros, L < 135)
    # o si es una perforación (pequeña, blanca y rodeada de metal, no de madera)
    madera = croma > 13
    idx = np.arange(1, n + 1)
    tam = ndi.sum(np.ones_like(L), lab, idx)
    luz = ndi.mean(L, lab, idx)
    color = ndi.mean(croma, lab, idx)        # el fondo es gris puro; los brillos de la madera, algo cálidos
    del_borde = set(borde.tolist())
    for k, caja in enumerate(ndi.find_objects(lab), start=1):
        t, l = tam[k - 1], luz[k - 1]
        if caja is None or k in del_borde or t < 12:
            continue
        # grandes (fondo y suelo vistos entre las piezas): admiten algo del tono de la
        # madera que reflejan; pequeñas: solo gris puro (si no, son brillos de la madera)
        if t >= 600 and l >= 150 and color[k - 1] < 8:
            fondo[caja] |= lab[caja] == k
        elif t >= 3000 and l >= 100 and color[k - 1] < 4:
            # sombra gris del suelo vista entre las piezas: es tan oscura como las caras
            # de los perfiles, pero ancha y compacta (los perfiles son tiras alargadas)
            m = lab[caja] == k
            if ndi.distance_transform_edt(m).max() > 18 and alargamiento(m) < 2.5:
                fondo[caja] |= m
        elif t < 600 and l >= 232 and color[k - 1] < 3:
            # se amplía el recuadro 3 px para ver qué la rodea
            y0, y1 = max(caja[0].start - 3, 0), caja[0].stop + 3
            x0, x1 = max(caja[1].start - 3, 0), caja[1].stop + 3
            m = lab[y0:y1, x0:x1] == k
            anillo = ndi.binary_dilation(m, iterations=2) & ~m
            # perforación: rodeada de metal oscuro (un brillo de la madera tiene madera o luz alrededor)
            if madera[y0:y1, x0:x1][anillo].mean() < 0.3 and L[y0:y1, x0:x1][anillo].mean() < 150:
                fondo[y0:y1, x0:x1] |= m
    # las sombras de contacto tienen borde nítido: el fondo se extiende a los píxeles
    # neutros y claros que lo tocan (los perfiles son más oscuros y no se ven afectados)
    crecer = (croma < 4) & (L > 150)
    fondo = ndi.binary_propagation(fondo, mask=fondo | crecer)
    pieza = ~fondo
    # contorno sin muescas: se rellenan entrantes de menos de ~6 px (los bordes de la
    # madera que el render quema en blanco contra el fondo blanco)
    # (solo junto a la madera: las rendijas de fondo entre dos perfiles se quedan abiertas)
    disco = np.hypot(*np.mgrid[-3:4, -3:4]) <= 3
    cerca_madera = ndi.uniform_filter(madera.astype(np.float32), 7) > 0.3
    pieza = pieza | (ndi.binary_closing(pieza, structure=disco) & (cerca_madera | (croma >= 3)))
    # huecos pequeños dentro de la madera (el fondo se cuela por un borde quemado):
    # se rellenan; los rodeados de metal oscuro son perforaciones y se quedan
    huecos = ndi.binary_fill_holes(pieza) & ~pieza
    labh, nh = ndi.label(huecos)
    for k, caja in enumerate(ndi.find_objects(labh), start=1):
        if caja is None:
            continue
        y0, y1 = max(caja[0].start - 3, 0), caja[0].stop + 3
        x0, x1 = max(caja[1].start - 3, 0), caja[1].stop + 3
        m = labh[y0:y1, x0:x1] == k
        if m.sum() > 250:
            continue
        anillo = ndi.binary_dilation(m, iterations=2) & ~m
        if L[y0:y1, x0:x1][anillo].mean() > 170:
            pieza[y0:y1, x0:x1] |= m
    lab3, n3 = ndi.label(pieza)
    if n3:
        tam3 = ndi.sum(np.ones_like(L), lab3, range(1, n3 + 1))
        pieza = np.isin(lab3, np.where(tam3 > 150)[0] + 1)
    fondo = ~pieza

    # color del fondo en cada punto (para el borde y para quitar el halo)
    peso = fondo.astype(np.float32)
    suma = ndi.gaussian_filter(peso, 6) + 1e-6
    fondo_rgb = np.stack([ndi.gaussian_filter(im[..., c] * peso, 6) for c in range(3)], -1) / suma[..., None]
    fondo_rgb[suma < 1e-3] = 247

    # 2. brillos blancos dentro de la pieza → hacia el color de la madera de alrededor
    if suavizar_brillos:
        brillo = pieza & (L > 226) & (croma < 12) & ~ndi.binary_dilation(fondo, iterations=3)
        madera = pieza & ~brillo & (croma > 14) & (L > 120)
        pm = madera.astype(np.float32)
        s = ndi.gaussian_filter(pm, 14) + 1e-6
        local = np.stack([ndi.gaussian_filter(im[..., c] * pm, 14) for c in range(3)], -1) / s[..., None]
        ok = brillo & (s > 0.05)
        t = np.clip((L - 220) / 30, 0, 1)[..., None] * 0.75   # cuanto más blanco, más se corrige
        aclarado = local * 1.08
        im = np.where(ok[..., None], im * (1 - t) + aclarado * t, im)

    # 3. transparencia gradual en una banda de 2 px alrededor del contorno
    dentro = ndi.binary_erosion(pieza, iterations=2)
    banda = pieza & ~dentro
    alfa = pieza.astype(np.float32)
    dif = np.linalg.norm(im - fondo_rgb, axis=2)
    alfa[banda] = np.clip(dif[banda] / 45.0, 0, 1)
    alfa = np.maximum(alfa, dentro.astype(np.float32))
    # sin halo: color real = fondo + (color - fondo) / alfa
    a = np.maximum(alfa, 1e-3)[..., None]
    limpio = np.where(banda[..., None], fondo_rgb + (im - fondo_rgb) / a, im)
    limpio = np.clip(limpio, 0, 255)

    rgba = np.dstack([limpio, alfa * 255]).astype(np.uint8)
    out = Image.fromarray(rgba, 'RGBA')

    # 4. recorte al contenido (+ margen) y proporción opcional
    ys, xs = np.where(alfa > 0.5)
    m = int(0.02 * max(h, w))
    caja = (max(xs.min() - m, 0), max(ys.min() - m, 0), min(xs.max() + m, w), min(ys.max() + m, h))
    out = out.crop(caja)
    if aspecto:
        cw, ch = out.size
        if cw / ch < aspecto:
            nw, nh = int(round(ch * aspecto)), ch
        else:
            nw, nh = cw, int(round(cw / aspecto))
        lienzo = Image.new('RGBA', (nw, nh), (0, 0, 0, 0))
        lienzo.paste(out, ((nw - cw) // 2, (nh - ch) // 2))
        out = lienzo
    if max(out.size) > max_lado:
        out.thumbnail((max_lado, max_lado), Image.LANCZOS)
    out.save(salida, optimize=True)
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    recortar(args[0], args[1], float(args[2]) if len(args) > 2 else None,
             suavizar_brillos='--sin-brillos' not in sys.argv)
