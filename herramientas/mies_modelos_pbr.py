"""Modelos 3D de MIES con materiales realistas.

- Aristas vivas (cada cara con su normal): las baldas y los perfiles no se ven
  «redondeados» como cuando se fusionan los vértices.
- Coordenadas de textura calculadas en el sistema del módulo: la veta del chopo va
  a lo largo de cada balda y el cepillado del aluminio, a lo largo de cada perfil.
- Materiales PBR con texturas (color, rugosidad/metal y relieve) guardadas aparte en
  public/modelos/texturas/: los cuatro modelos las comparten y el navegador las
  descarga una sola vez. Se generan con herramientas/mies_texturas.py.
- En el pentágono: una cuerda de yute tensada por las perforaciones de los perfiles
  exteriores, con una lámina A1 (la de MIES) colgada con dos pinzas de madera.

Uso: python3 herramientas/mies_modelos_pbr.py <carpeta con los .glb de cascadio> [lámina A1 en .jpg]
     (expositor_tabla_inferior/media/superior.glb y expositor_todopentagono.glb,
      convertidos de los STEP; están en Z arriba y en metros)
"""
import os
import sys
import json
import numpy as np
import trimesh
import pygltflib as G
from PIL import Image

ORIGEN = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/glb'
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SALIDA = os.path.join(RAIZ, 'public', 'modelos')
LAMINA = os.path.join(RAIZ, 'public', 'modelos', 'texturas', 'lamina-mies-a1.jpg')
rng = np.random.default_rng(3)


# ── Lectura ──────────────────────────────────────────────────────────────────
def piezas(nombre):
    s = trimesh.load(os.path.join(ORIGEN, nombre))
    out = []
    for nodo in s.graph.nodes_geometry:
        T, g = s.graph[nodo]
        m = s.geometry[g].copy()
        m.apply_transform(T)
        out.append((nodo, m))
    return out


# ── Geometría con UV (en Z arriba, sistema del módulo) ───────────────────────
class Trozo:
    """Triángulos sueltos (cada cara con sus vértices) de un solo material."""

    def __init__(self, material, pos, nor, uv):
        self.material, self.pos, self.nor, self.uv = material, pos, nor, uv

    def transformar(self, M):
        R = M[:3, :3]
        self.pos = self.pos @ R.T + M[:3, 3]
        self.nor = self.nor @ R.T
        return self


def sueltos(m, caras):
    tri = m.triangles[caras]                      # (n, 3, 3)
    nor = np.repeat(m.face_normals[caras][:, None, :], 3, axis=1)
    return tri.reshape(-1, 3), nor.reshape(-1, 3)


def tangente_h(n):
    """Dirección horizontal dentro de la cara (para las caras verticales)."""
    t = np.stack([-n[:, 1], n[:, 0], np.zeros(len(n))], 1)
    largo = np.linalg.norm(t, axis=1, keepdims=True)
    t = np.where(largo > 1e-6, t / np.maximum(largo, 1e-9), [1, 0, 0])
    return t


def madera(m):
    """Balda o base de contrachapado: cara (veta) y canto (chapas)."""
    n = m.face_normals
    cara = np.abs(n[:, 2]) > 0.9
    trozos = []
    ox, oy = rng.uniform(0, 1, 2)
    if cara.any():
        p, nn = sueltos(m, cara)
        uv = np.stack([p[:, 0] + ox, p[:, 1] * 1.0 + oy], 1)   # veta a lo largo de x
        trozos.append(Trozo('chopo_cara', p, nn, uv))
    if (~cara).any():
        p, nn = sueltos(m, ~cara)
        t = np.repeat(tangente_h(m.face_normals[~cara]), 3, axis=0)
        z0, z1 = m.bounds[0][2], m.bounds[1][2]
        uv = np.stack([(p * t).sum(1) / 0.5 + ox, (z1 - p[:, 2]) / (z1 - z0)], 1)
        trozos.append(Trozo('chopo_canto', p, nn, uv))
    return trozos


def aluminio(m):
    p, nn = sueltos(m, np.ones(len(m.faces), bool))
    t = np.repeat(tangente_h(m.face_normals), 3, axis=0)
    off = rng.uniform(0, 1)
    uv = np.stack([(p * t).sum(1) / 0.2 + off, p[:, 2] / 1.0], 1)   # cepillado a lo largo
    return [Trozo('aluminio', p, nn, uv)]


def pieza(nombre, m):
    return aluminio(m) if nombre.startswith('Part1') else madera(m)


def caja(material, c, tam, uv_escala=1.0, uv_de=None):
    """Caja alineada con los ejes: centro c, tamaño tam (x, y, z)."""
    m = trimesh.creation.box(extents=tam)
    m.apply_translation(c)
    p, nn = sueltos(m, np.ones(len(m.faces), bool))
    if uv_de is None:
        # proyección por la cara dominante
        a = np.argmax(np.abs(nn), axis=1)
        uv = np.where(a[:, None] == 0, p[:, [1, 2]], np.where(a[:, None] == 1, p[:, [0, 2]], p[:, [0, 1]]))
        uv = uv / uv_escala
    else:
        uv = uv_de(p, nn)
    return Trozo(material, p, nn, uv)


def tubo(puntos, radio, lados=14, material='cuerda', paso=0.04):
    """Tubo suave a lo largo de una polilínea (la cuerda)."""
    P = np.asarray(puntos)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    ref = np.array([0, 0, 1.0])
    pos, nor, uv = [], [], []
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    anillos = []
    for i, (p, t) in enumerate(zip(P, T)):
        b = np.cross(t, ref)
        b /= np.linalg.norm(b)
        nrm = np.cross(b, t)
        ang = np.linspace(0, 2 * np.pi, lados + 1)
        dirs = np.cos(ang)[:, None] * b + np.sin(ang)[:, None] * nrm
        anillos.append((p + dirs * radio, dirs, np.stack([ang / (2 * np.pi), np.full(lados + 1, s[i] / paso)], 1)))
    for i in range(len(P) - 1):
        (a, na, ua), (b, nb, ub) = anillos[i], anillos[i + 1]
        for j in range(lados):
            for tri in [((a, na, ua), j), ((b, nb, ub), j), ((b, nb, ub), j + 1),
                        ((a, na, ua), j), ((b, nb, ub), j + 1), ((a, na, ua), j + 1)]:
                (q, nq, uq), k = tri
                pos.append(q[k]); nor.append(nq[k]); uv.append(uq[k])
    return Trozo(material, np.array(pos), np.array(nor), np.array(uv))


def esfera(c, r, material):
    m = trimesh.creation.icosphere(subdivisions=2, radius=r)
    m.apply_translation(c)
    p = m.vertices[m.faces].reshape(-1, 3)
    nn = (p - c) / r
    uv = np.stack([np.arctan2(nn[:, 1], nn[:, 0]) / (2 * np.pi), nn[:, 2] * 0.3], 1)
    return Trozo(material, p, nn, uv)


# ── Cuerda con la lámina A1, en la parte de atrás (sistema del módulo) ──────
# En el sistema del módulo, y = 0 es la cara ancha (delante, hacia fuera del
# pentágono) e y = 0,3 la estrecha (atrás). Los perfiles traseros (Part1.3 y
# Part1.4) tienen la esquina hacia atrás y una perforación a 1,70 m en el ala
# trasera: la cuerda sale por ellas, corre por detrás de los perfiles y la lámina
# cuelga detrás, mirando hacia delante. Así, desde fuera, la maqueta de la balda
# queda delante y la lámina de fondo.
def agujero_trasero(perfil):
    """Centro (x, y, z) de la perforación alta del ala trasera (eje del agujero en y)."""
    f = perfil.triangles_center
    n = perfil.face_normals
    y1 = perfil.bounds[1][1]
    sel = ((f[:, 2] > 1.6) & (f[:, 2] < 1.76) & (np.abs(n[:, 1]) < 0.05)
           & (f[:, 1] > y1 - 0.006) & (perfil.area_faces < 1e-4))
    c = f[sel]
    return c[:, 0].mean(), y1, c[:, 2].mean()


def colgador(perfil_izq, perfil_der):
    xi, yb, z = agujero_trasero(perfil_izq)
    xd, _, _ = agujero_trasero(perfil_der)
    r = 0.0035
    yc = yb + r + 0.001                    # la cuerda corre pegada por detrás de los perfiles
    caida = 0.012                          # cede un poco con el peso de la lámina
    pinzas = [-0.15, 0.15]
    xs = np.linspace(xi, xd, 81)
    zs = np.interp(xs, [xi, pinzas[0], pinzas[1], xd], [z, z - caida, z - caida * 1.05, z])
    zs -= 0.002 * np.sin(np.clip((xs - pinzas[0]) / (pinzas[1] - pinzas[0]), 0, 1) * np.pi)
    dentro = yb - 0.012                    # los extremos vuelven a entrar por el agujero
    tramo = [[xi, dentro, z], [xi, yb - 0.004, z]] + [[x, yc, zz] for x, zz in zip(xs, zs)] + \
            [[xd, yb - 0.004, z], [xd, dentro, z]]
    trozos = [tubo(np.array(tramo), r),
              esfera([xi, dentro - 0.004, z], 0.008, 'cuerda'),   # nudos por dentro
              esfera([xd, dentro - 0.004, z], 0.008, 'cuerda')]
    # lámina A1 (594 × 841 mm) sobre cartón pluma de 5 mm
    ancho, alto, grueso = 0.594, 0.841, 0.005
    yl = yc + r + grueso / 2 + 0.0005
    arriba = z - caida - 0.03

    def uv_lamina(p, nn):
        return np.stack([(p[:, 0] + ancho / 2) / ancho, (arriba - p[:, 2]) / alto], 1)

    tablero = caja('carton', [0, yl, arriba - alto / 2], [ancho, grueso, alto])
    frente = tablero.nor[:, 1] < -0.9      # la cara que mira hacia delante
    trozos.append(Trozo('lamina', tablero.pos[frente], tablero.nor[frente], uv_lamina(tablero.pos[frente], None)))
    trozos.append(Trozo('carton', tablero.pos[~frente], tablero.nor[~frente], tablero.uv[~frente]))
    # dos pinzas de madera que muerden la cuerda y el borde de la lámina
    for xp in pinzas:
        zc = z - caida - 0.014
        for y in (yc - r - 0.0025, yl + grueso / 2 + 0.0025):
            trozos.append(caja('pinza', [xp, y, zc], [0.011, 0.0045, 0.072], uv_escala=0.3))
    return trozos


# ── Maquetas para las baldas (sistema del módulo; z0 = cara de arriba de la balda)
def suave(m, material, escala_uv=0.3):
    """Malla con normales suaves (piezas curvas: lámpara, figura)."""
    p = m.vertices[m.faces].reshape(-1, 3)
    nn = m.vertex_normals[m.faces].reshape(-1, 3)
    uv = np.stack([p[:, 0] + p[:, 1], p[:, 2]], 1) / escala_uv
    return Trozo(material, p, nn, uv)


def peana(z0, ancho, fondo, cy=0.13, alto=0.006, material='carton_gris'):
    return caja(material, [0, cy, z0 + alto / 2], [ancho, fondo, alto]), z0 + alto


def maqueta_ciudad(z0):
    """Maqueta de arquitectura: manzana de bloques de cartón blanco y una plaza de balsa."""
    t, z = peana(z0, 0.30, 0.20)
    trozos = [t]
    r = np.random.default_rng(11)
    for i, x in enumerate(np.linspace(-0.115, 0.115, 5)):
        for j, y in enumerate([0.075, 0.13, 0.185]):
            if (i, j) in [(2, 1), (1, 1)]:
                continue                       # hueco para la plaza
            a = r.uniform(0.032, 0.046)
            b = r.uniform(0.03, 0.044)
            h = r.choice([0.03, 0.05, 0.07, 0.1, 0.14]) * (1.3 if (i, j) == (3, 0) else 1)
            trozos.append(caja('carton', [x, y, z + h / 2], [a, b, h], uv_escala=0.2))
    trozos.append(caja('pinza', [-0.03, 0.13, z + 0.0015], [0.1, 0.045, 0.003], uv_escala=0.25))
    return trozos


def maqueta_silla(z0):
    """Silla a escala 1:5 en balsa, sobre una peana blanca."""
    t, z = peana(z0, 0.15, 0.15, material='carton')
    trozos = [t]
    a, h = 0.088, 0.09
    for sx in (-1, 1):
        for sy in (-1, 1):
            trozos.append(caja('pinza', [sx * (a / 2 - 0.004), 0.13 + sy * (a / 2 - 0.004), z + h / 2], [0.006, 0.006, h], uv_escala=0.2))
    trozos.append(caja('pinza', [0, 0.13, z + h + 0.003], [a, a, 0.006], uv_escala=0.2))
    trozos.append(caja('pinza', [0, 0.13 + a / 2 - 0.003, z + h + 0.05], [a, 0.006, 0.08], uv_escala=0.2))
    return trozos


def maqueta_lampara(z0):
    """Prototipo de lámpara de sobremesa impreso en resina."""
    t, z = peana(z0, 0.16, 0.16, material='carton')
    perfil = np.array([[0, 0], [0.06, 0], [0.062, 0.006], [0.02, 0.016], [0.009, 0.03], [0.008, 0.18],
                       [0.015, 0.186], [0.075, 0.25], [0.078, 0.256], [0.07, 0.258], [0.012, 0.2], [0, 0.2]])
    m = trimesh.creation.revolve(perfil, sections=48)
    m.apply_translation([0, 0.13, z])
    return [t, suave(m, 'resina')]


def maqueta_torre(z0):
    """Torre de forjados que giran, de cartón blanco con núcleo de balsa."""
    t, z = peana(z0, 0.18, 0.15)
    trozos = [t, caja('pinza', [0, 0.13, z + 0.13], [0.026, 0.026, 0.26], uv_escala=0.2)]
    for k in range(13):
        ang = np.radians(7 * k)
        m = trimesh.creation.box(extents=[0.12, 0.075, 0.004])
        m.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
        m.apply_translation([0, 0.13, z + 0.01 + k * 0.02])
        p, nn = sueltos(m, np.ones(len(m.faces), bool))
        trozos.append(Trozo('carton', p, nn, p[:, :2] / 0.2))
    return trozos


def maqueta_mies(z0, piezas_modulo, escala=1 / 6):
    """El propio módulo MIES a escala 1:6, con sus tres baldas."""
    t, z = peana(z0, 0.21, 0.09, cy=0.12)
    trozos = [t]
    S = np.diag([escala, escala, escala, 1.0])
    S[:3, 3] = [0, 0.12 - 0.15 * escala, z]
    for n, m in piezas_modulo:
        trozos += [tr.transformar(S) for tr in pieza(n, m)]
    return trozos


# ── Figura humana a escala (1,75 m), como las de las maquetas de arquitectura ──
def figura(altura=1.75):
    from skimage.measure import marching_cubes

    def cono(p, a, b, ra, rb):                 # cono redondeado entre a y b
        a, b = np.array(a), np.array(b)
        ba = b - a
        pa = p - a
        h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
        d = np.linalg.norm(pa - h[..., None] * ba, axis=-1)
        return d - (ra + (rb - ra) * h)

    def elipsoide(p, c, r):
        q = (p - np.array(c)) / np.array(r)
        k0 = np.linalg.norm(q, axis=-1)
        k1 = np.linalg.norm(q / np.array(r), axis=-1)
        return k0 * (k0 - 1) / np.maximum(k1, 1e-9)

    def union(a, b, k=0.035):                  # unión suave
        h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
        return b * (1 - h) + a * h - k * h * (1 - h)

    paso = 0.012
    xs = np.arange(-0.36, 0.36, paso)
    ys = np.arange(-0.16, 0.26, paso)
    zs = np.arange(-0.01, 1.8, paso)
    P = np.stack(np.meshgrid(xs, ys, zs, indexing='ij'), -1)
    d = elipsoide(P, [0, 0.005, 1.635], [0.074, 0.088, 0.108])                       # cabeza
    d = union(d, cono(P, [0, 0, 1.46], [0, 0.01, 1.56], 0.052, 0.045))               # cuello
    d = union(d, elipsoide(P, [0, 0, 1.33], [0.185, 0.105, 0.16]), 0.05)            # pecho
    d = union(d, elipsoide(P, [0, 0.005, 1.13], [0.155, 0.095, 0.17]), 0.06)        # vientre
    d = union(d, elipsoide(P, [0, -0.005, 0.95], [0.17, 0.11, 0.12]), 0.05)         # cadera
    for s in (-1, 1):
        d = union(d, cono(P, [s * 0.165, 0, 1.415], [s * 0.215, -0.005, 1.15], 0.055, 0.042))   # brazo
        d = union(d, cono(P, [s * 0.215, -0.005, 1.15], [s * 0.235, 0.03, 0.9], 0.04, 0.031))  # antebrazo
        d = union(d, elipsoide(P, [s * 0.24, 0.04, 0.83], [0.024, 0.042, 0.075]), 0.02)      # mano
        d = union(d, cono(P, [s * 0.09, 0, 0.93], [s * 0.1, 0.012, 0.5], 0.088, 0.056))      # muslo
        d = union(d, cono(P, [s * 0.1, 0.012, 0.5], [s * 0.105, -0.005, 0.085], 0.055, 0.036))  # pierna
        d = union(d, cono(P, [s * 0.105, -0.03, 0.04], [s * 0.115, 0.15, 0.025], 0.042, 0.03), 0.03)  # pie
    d = np.maximum(d, -P[..., 2])              # planta de los pies en el suelo
    v, f, _, _ = marching_cubes(d, 0.0, spacing=(paso, paso, paso))
    v += [xs[0], ys[0], zs[0]]
    m = trimesh.Trimesh(v, f[:, ::-1], process=True)
    m = max(m.split(only_watertight=False), key=lambda c: len(c.faces))   # sin trocitos sueltos
    trimesh.smoothing.filter_taubin(m, iterations=12)
    m.apply_scale(altura / 1.75)
    m.fix_normals()
    return m


# ── Escritura del glTF (texturas como archivos aparte) ──────────────────────
TEX = {
    'chopo_cara': ('chopo-cara', 0.7),
    'chopo_canto': ('chopo-canto', 0.8),
    'aluminio': ('aluminio', 0.3),
    'cuerda': ('cuerda', 1.0),
    'pinza': ('chopo-cara', 0.5),
}
SIMPLES = {
    # nombre: (color sRGB, rugosidad, imagen de color)
    'carton': ((238, 237, 232), 0.85, None),
    'carton_gris': ((132, 130, 124), 0.9, None),
    'resina': ((232, 230, 224), 0.38, None),
    'figura': ((176, 172, 164), 0.75, None),
    'lamina': ((255, 255, 255), 0.62, 'texturas/lamina-mies-a1.jpg'),
}


def lineal(c):
    c = np.asarray(c) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).tolist()


def escribir(trozos, ruta):
    # Z arriba → Y arriba, apoyar en el suelo y centrar en planta
    R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
    for t in trozos:
        t.pos = t.pos @ R.T
        t.nor = t.nor @ R.T
    todo = np.vstack([t.pos for t in trozos])
    lo, hi = todo.min(0), todo.max(0)
    d = np.array([-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2])
    for t in trozos:
        t.pos = t.pos + d

    gl = G.GLTF2(asset=G.Asset(generator='MIES · mies_modelos_pbr.py', version='2.0'))
    gl.samplers = [G.Sampler(magFilter=9729, minFilter=9987, wrapS=10497, wrapT=10497)]
    datos = bytearray()
    imagenes, texturas, materiales = {}, {}, {}

    def textura(uri):
        if uri not in texturas:
            imagenes[uri] = len(gl.images)
            gl.images.append(G.Image(uri=uri))
            texturas[uri] = len(gl.textures)
            gl.textures.append(G.Texture(sampler=0, source=imagenes[uri]))
        return texturas[uri]

    def material(nombre):
        if nombre in materiales:
            return materiales[nombre]
        if nombre in TEX:
            base, relieve = TEX[nombre]
            mat = G.Material(
                name=nombre,
                pbrMetallicRoughness=G.PbrMetallicRoughness(
                    baseColorTexture=G.TextureInfo(index=textura(f'texturas/{base}-color.jpg')),
                    metallicRoughnessTexture=G.TextureInfo(index=textura(f'texturas/{base}-orm.jpg')),
                    metallicFactor=1.0, roughnessFactor=1.0),
                normalTexture=G.NormalMaterialTexture(index=textura(f'texturas/{base}-normal.jpg'), scale=relieve),
            )
        else:
            color, rug, img = SIMPLES[nombre]
            pbr = G.PbrMetallicRoughness(baseColorFactor=lineal(color) + [1.0], metallicFactor=0.0, roughnessFactor=rug)
            if img:
                pbr.baseColorTexture = G.TextureInfo(index=textura(img))
            mat = G.Material(name=nombre, pbrMetallicRoughness=pbr)
        materiales[nombre] = len(gl.materials)
        gl.materials.append(mat)
        return materiales[nombre]

    def vista(arr, objetivo=None):
        nonlocal datos
        while len(datos) % 4:
            datos += b'\0'
        ini = len(datos)
        datos += arr.tobytes()
        gl.bufferViews.append(G.BufferView(buffer=0, byteOffset=ini, byteLength=arr.nbytes, target=objetivo))
        return len(gl.bufferViews) - 1

    # un primitivo por material (menos llamadas de dibujo)
    grupos = {}
    for t in trozos:
        grupos.setdefault(t.material, []).append(t)
    prims = []
    for nombre, lista in grupos.items():
        pos = np.vstack([t.pos for t in lista]).astype(np.float32)
        nor = np.vstack([t.nor for t in lista]).astype(np.float32)
        nor /= np.linalg.norm(nor, axis=1, keepdims=True)
        uv = np.vstack([t.uv for t in lista]).astype(np.float32)
        # unir vértices idénticos (posición, normal y uv) para aligerar
        clave = np.hstack([np.round(pos, 6), np.round(nor, 4), np.round(uv, 5)])
        _, unicos, inv = np.unique(clave, axis=0, return_index=True, return_inverse=True)
        pos, nor, uv = pos[unicos], nor[unicos], uv[unicos]
        idx = inv.reshape(-1).astype(np.uint32)
        acc = []
        for arr, tipo, objetivo in [(pos, 'VEC3', 34962), (nor, 'VEC3', 34962), (uv, 'VEC2', 34962)]:
            v = vista(arr, objetivo)
            gl.accessors.append(G.Accessor(bufferView=v, componentType=5126, count=len(arr), type=tipo,
                                           min=arr.min(0).tolist() if tipo == 'VEC3' else None,
                                           max=arr.max(0).tolist() if tipo == 'VEC3' else None))
            acc.append(len(gl.accessors) - 1)
        v = vista(idx, 34963)
        gl.accessors.append(G.Accessor(bufferView=v, componentType=5125, count=len(idx), type='SCALAR'))
        prims.append(G.Primitive(attributes=G.Attributes(POSITION=acc[0], NORMAL=acc[1], TEXCOORD_0=acc[2]),
                                 indices=len(gl.accessors) - 1, material=material(nombre)))
    gl.meshes = [G.Mesh(name='mies', primitives=prims)]
    gl.nodes = [G.Node(name='mies', mesh=0)]
    gl.scenes = [G.Scene(nodes=[0])]
    gl.scene = 0
    gl.buffers = [G.Buffer(byteLength=len(datos))]
    gl.set_binary_blob(bytes(datos))
    gl.save_binary(ruta)
    print(os.path.basename(ruta), os.path.getsize(ruta) // 1024, 'KB', 'medidas (mm):', ((hi - lo) * 1000).round().tolist())


# ── Montaje ──────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(LAMINA):
        # la lámina de entrega en JPG (no está en el repositorio: se pasa como 2.º argumento)
        im = Image.open(sys.argv[2]).convert('RGB')
        im.thumbnail((1448, 2048), Image.LANCZOS)
        im.save(LAMINA, quality=86, optimize=True, progressive=True)

    inf = piezas('expositor_tabla_inferior.glb')
    med = piezas('expositor_tabla_media.glb')
    sup = piezas('expositor_tabla_superior.glb')
    for _, m in med:
        m.apply_translation([0, 0, 1.2])          # misma referencia que las otras dos

    # Módulo suelto con cada tipo de balda
    for nombre, lista in [('inferior', inf), ('media', med), ('superior', sup)]:
        trozos = []
        for n, m in lista:
            trozos += pieza(n, m)
        escribir(trozos, os.path.join(SALIDA, f'mies-{nombre}.glb'))

    # Pentágono: cada módulo con una balda distinta; los módulos con la balda de
    # abajo llevan la cuerda con la lámina A1 (así la lámina no choca con nada)
    pen = dict(piezas('expositor_todopentagono.glb'))
    ref = pen['base.1_4']
    a_ref = np.eye(4)
    a_ref[2, 3] = -1.2                             # módulo suelto → módulo base.1_4
    balda = {k: [m for n, m in l if n.startswith('Part2')][0] for k, l in [('inferior', inf), ('media', med), ('superior', sup)]}
    perfiles = {n: m for n, m in inf if n.startswith('Part1')}
    sufijo = lambda n: ('_' + n.split('.')[1].split('_', 1)[1]) if '_' in n.split('.')[1] else ''
    sufijos = sorted({sufijo(n) for n in pen if n.startswith('base')})
    orden = ['inferior', 'media', 'superior', 'inferior', 'media']
    trozos, marcos = [], []
    # el módulo completo (base, perfiles y las tres baldas), para la maqueta a escala
    modulo_completo = [(n, m) for n, m in inf] + [('balda', balda['media']), ('balda', balda['superior'])]
    for i, suf in enumerate(sufijos):
        M, _, _ = trimesh.registration.procrustes(ref.vertices, pen['base.1' + suf].vertices,
                                                  reflection=False, scale=False, return_cost=True)
        M = M @ a_ref                              # módulo suelto → su sitio en el pentágono
        Mi = np.linalg.inv(M)
        for n, m in pen.items():
            if sufijo(n) != suf or n.startswith('Part2'):
                continue
            local = m.copy()
            local.apply_transform(Mi)              # UV en el sistema del módulo
            trozos += [t.transformar(M) for t in pieza(n, local)]
        trozos += [t.transformar(M) for t in pieza('balda', balda[orden[i]])]
        if orden[i] == 'inferior':
            trozos += [t.transformar(M) for t in colgador(perfiles['Part1.3'], perfiles['Part1.4'])]
        # una maqueta en cada balda (delante de la lámina en los módulos que la llevan)
        z0 = balda[orden[i]].bounds[1][2]
        maqueta = MAQUETAS[i](z0) if MAQUETAS[i] is not maqueta_mies else maqueta_mies(z0, modulo_completo)
        trozos += [t.transformar(M) for t in maqueta]
        marcos.append(M)
    # figura humana de 1,75 m delante del primer módulo, algo a un lado, mirándolo
    M = marcos[FIGURA[0]]
    R = M[:3, :3]
    frente = M[:3, 3]                               # centro de la cara ancha del módulo
    fuera, lado = -R[:, 1], R[:, 0]
    pos = frente + fuera * FIGURA[1] + lado * FIGURA[2]
    mira = frente + lado * 0.1 - pos
    ang = np.arctan2(-mira[0], mira[1])
    T = trimesh.transformations.rotation_matrix(ang, [0, 0, 1])
    T[:3, 3] = [pos[0], pos[1], frente[2]]
    trozos.append(suave(figura(), 'figura').transformar(T))
    escribir(trozos, os.path.join(SALIDA, 'mies-pentagono.glb'))


# maqueta de cada módulo del pentágono (en el orden de las baldas: inferior,
# media, superior, inferior, media) y figura: (módulo, distancia delante, desplazamiento lateral)
MAQUETAS = [maqueta_ciudad, maqueta_silla, maqueta_lampara, maqueta_mies, maqueta_torre]
FIGURA = (0, 0.7, 0.62)

if __name__ == '__main__':
    main()
