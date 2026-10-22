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


# ── Cuerda con la lámina A1 (sistema del módulo) ─────────────────────────────
def agujero(perfil):
    """Centro (y, z) de la perforación alta del ala perpendicular a x."""
    f = perfil.triangles_center
    n = perfil.face_normals
    x0 = perfil.bounds[0][0]
    pequenas = perfil.area_faces < 1e-4          # las paredes del agujero son caras pequeñas
    sel = (f[:, 2] > 1.6) & (f[:, 2] < 1.76) & (np.abs(n[:, 0]) < 0.05) & (f[:, 0] < x0 + 0.006) & pequenas
    c = f[sel]
    return c[:, 1].mean(), c[:, 2].mean()


def colgador(perfil_izq, perfil_der):
    y, z = agujero(perfil_izq)
    xi = perfil_izq.bounds[0][0]           # cara exterior del ala con el agujero
    xd = perfil_der.bounds[1][0]
    caida = 0.014                          # la cuerda cede con el peso de la lámina
    xs = np.linspace(xi - 0.012, xd + 0.012, 121)
    pinzas = [-0.2, 0.2]
    # perfil de la cuerda: recta entre los apoyos (perfiles y pinzas), algo combada
    apoyos_x = [xi, pinzas[0], pinzas[1], xd]
    apoyos_z = [z, z - caida, z - caida * 1.05, z]
    zs = np.interp(xs, apoyos_x, apoyos_z)
    zs -= 0.003 * np.sin(np.clip((xs - pinzas[0]) / (pinzas[1] - pinzas[0]), 0, 1) * np.pi)
    cuerda = tubo(np.stack([xs, np.full_like(xs, y), zs], 1), 0.0035)
    trozos = [cuerda,
              esfera([xi - 0.014, y, z], 0.008, 'cuerda'),      # nudos por fuera
              esfera([xd + 0.014, y, z], 0.008, 'cuerda')]
    # lámina A1 (594 × 841 mm) sobre cartón pluma de 5 mm
    ancho, alto, grueso = 0.594, 0.841, 0.005
    arriba = z - caida - 0.028
    c = [0, y, arriba - alto / 2]

    def uv_lamina(p, nn):
        return np.stack([(p[:, 0] + ancho / 2) / ancho, (arriba - p[:, 2]) / alto], 1)

    tablero = caja('carton', c, [ancho, grueso, alto])
    frente = tablero.nor[:, 1] < -0.9      # la cara que mira hacia fuera del pentágono
    trozos.append(Trozo('lamina', tablero.pos[frente], tablero.nor[frente], uv_lamina(tablero.pos[frente], None)))
    trozos.append(Trozo('carton', tablero.pos[~frente], tablero.nor[~frente], tablero.uv[~frente]))
    # dos pinzas de madera que muerden la cuerda y el borde de la lámina
    for xp in pinzas:
        zc = z - caida - 0.012
        for dy in (-0.0055, 0.0055):
            trozos.append(caja('pinza', [xp, y + dy, zc], [0.011, 0.0045, 0.072], uv_escala=0.3))
    return trozos


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
    trozos = []
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
            trozos += [t.transformar(M) for t in colgador(perfiles['Part1.1'], perfiles['Part1.2'])]
    escribir(trozos, os.path.join(SALIDA, 'mies-pentagono.glb'))


if __name__ == '__main__':
    main()
