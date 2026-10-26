"""Modelos 3D de OVUM G-1 para el visor de la web.

Parte del .obj que Martín exportó de Fusion (en cm, Z arriba, cuatro grupos:
«puente» = frontal, «Body34» = puente nasal y «1.pat (1)» / «1.pat (1) (1)» = patillas)
y crea dos .glb en metros, Y arriba y con el frontal mirando a +Z:

- ovum-g1.glb: las gafas montadas.
- ovum-g1-montaje.glb: animación en bucle de 7 s; las piezas se separan en despiece
  (puente nasal hacia abajo y delante, patillas hacia atrás y hacia fuera), se quedan
  quietas un momento y vuelven a encajar.

Material: biocerámica de cáscara de huevo, color hueso mate con motas y poro fino
(textura y mapa de normales generados aquí, repetibles, con proyección en caja).

Uso: python3 herramientas/ovum_modelo.py <gafasdef.obj> [carpeta de salida]
"""
import io
import os
import sys
import numpy as np
import pygltflib as G
from PIL import Image
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ovum_obj import leer

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ORIGEN = sys.argv[1]
SALIDA = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, 'public', 'modelos')
TESELA = 0.05  # m que ocupa una repetición de la textura
rng = np.random.default_rng(11)

# ---------- geometría ----------
NOMBRES = {'puente': 'frontal', 'Body34': 'puente nasal', '1.pat (1)': 'patilla izquierda', '1.pat (1) (1)': 'patilla derecha'}
R = np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], float)  # (x, y, z) del .obj -> (-y, z, -x)
piezas = {}
for g, (p, n, f) in leer(ORIGEN).items():
    piezas[NOMBRES[g]] = [(p @ R.T) * 0.01, None if n is None else n @ R.T, f]
todo = np.vstack([v[0] for v in piezas.values()])
base = np.array([(todo[:, 0].min() + todo[:, 0].max()) / 2, todo[:, 1].min(), (todo[:, 2].min() + todo[:, 2].max()) / 2])
for v in piezas.values():
    v[0] = v[0] - base
todo = todo - base
print('tamaño (mm):', (np.ptp(todo, 0) * 1000).round(1))


def normales(p, f):
    n = np.zeros_like(p)
    fn = np.cross(p[f[:, 1]] - p[f[:, 0]], p[f[:, 2]] - p[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def uv_caja(p, n):
    eje = np.abs(n).argmax(1)
    u = np.where(eje == 0, p[:, 2], p[:, 0])
    v = np.where(eje == 1, p[:, 2], p[:, 1])
    return np.stack([u, v], 1) / TESELA


# ---------- textura de cáscara ----------
def ruido(t, sigma):
    return nd.gaussian_filter(rng.standard_normal((t, t)), sigma, mode='wrap')


def texturas(t=1024):
    grano = ruido(t, 1.2) * 0.6 + ruido(t, 6) * 1.4 + ruido(t, 30) * 3
    grano = (grano - grano.mean()) / grano.std()
    color = np.array([214, 208, 194], float)[None, None] * (1 + 0.035 * grano[..., None])
    # motas oscuras (marrones) y algunas claras, repartidas sin patrón
    for n_, tono, r_max in ((900, (105, 82, 62), 4.5), (2500, (150, 128, 105), 1.8), (500, (238, 234, 224), 2.5)):
        ys, xs = rng.integers(0, t, n_), rng.integers(0, t, n_)
        rad = rng.uniform(0.7, r_max, n_)
        yy, xx = np.mgrid[-6:7, -6:7]
        for y, x, r in zip(ys, xs, rad):
            a = np.clip(r + 0.5 - np.hypot(yy, xx), 0, 1) * rng.uniform(0.45, 0.9)
            iy, ix = (y + yy) % t, (x + xx) % t
            color[iy, ix] = color[iy, ix] * (1 - a[..., None]) + np.array(tono) * a[..., None]
    alto = grano * 0.6 + ruido(t, 0.8) * 2.5
    gy, gx = np.gradient(alto)
    k = 0.9
    nrm = np.dstack([-gx * k, -gy * k, np.ones_like(gx)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    def jpg(a):
        b = io.BytesIO()
        Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(b, 'JPEG', quality=88)
        return b.getvalue()
    return jpg(color), jpg((nrm * 0.5 + 0.5) * 255)


COLOR, NORMAL = texturas()


# ---------- glTF ----------
def construir(animar):
    gltf = G.GLTF2(asset=G.Asset(generator='ovum_modelo.py'))
    datos = bytearray()

    def vista(b, objetivo=None):
        while len(datos) % 4:
            datos.append(0)
        gltf.bufferViews.append(G.BufferView(buffer=0, byteOffset=len(datos), byteLength=len(b), target=objetivo))
        datos.extend(b)
        return len(gltf.bufferViews) - 1

    def accesor(arr, tipo, objetivo=None, minmax=False):
        comp = G.UNSIGNED_INT if arr.dtype == np.uint32 else G.FLOAT
        a = G.Accessor(bufferView=vista(arr.tobytes(), objetivo), componentType=comp, count=len(arr), type=tipo)
        if minmax:
            a.min = arr.min(0).tolist() if arr.ndim > 1 else [float(arr.min())]
            a.max = arr.max(0).tolist() if arr.ndim > 1 else [float(arr.max())]
        gltf.accessors.append(a)
        return len(gltf.accessors) - 1

    for i, b in enumerate((COLOR, NORMAL)):
        gltf.images.append(G.Image(bufferView=vista(b), mimeType='image/jpeg'))
        gltf.textures.append(G.Texture(source=i, sampler=0))
    gltf.samplers.append(G.Sampler(wrapS=G.REPEAT, wrapT=G.REPEAT, magFilter=G.LINEAR, minFilter=G.LINEAR_MIPMAP_LINEAR))
    gltf.materials.append(G.Material(
        name='Biocerámica de cáscara de huevo',
        pbrMetallicRoughness=G.PbrMetallicRoughness(baseColorTexture=G.TextureInfo(index=0), metallicFactor=0.0, roughnessFactor=0.82),
        normalTexture=G.NormalMaterialTexture(index=1, scale=0.6)))

    hijos, encuadre = [], None
    for nombre, (p, n, f) in piezas.items():
        if n is None:
            n = normales(p, f)
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        uv = uv_caja(p, n)
        prim = G.Primitive(
            attributes=G.Attributes(POSITION=accesor(p.astype(np.float32), 'VEC3', G.ARRAY_BUFFER, True),
                                    NORMAL=accesor(n.astype(np.float32), 'VEC3', G.ARRAY_BUFFER),
                                    TEXCOORD_0=accesor(uv.astype(np.float32), 'VEC2', G.ARRAY_BUFFER)),
            indices=accesor(f.astype(np.uint32).ravel(), 'SCALAR', G.ELEMENT_ARRAY_BUFFER), material=0)
        gltf.meshes.append(G.Mesh(name=nombre, primitives=[prim]))
        gltf.nodes.append(G.Node(name=nombre, mesh=len(gltf.meshes) - 1))
        hijos.append(len(gltf.nodes) - 1)

    if animar:
        # despiece: desplazamientos en m (x a la derecha, y arriba, z hacia delante)
        lado = lambda nombre: 1 if piezas[nombre][0][:, 0].mean() > 0 else -1
        despiece = {
            'frontal': [0, 0.012, 0],
            'puente nasal': [0, -0.035, 0.03],
            'patilla izquierda': [0.035 * lado('patilla izquierda'), 0.004, -0.06],
            'patilla derecha': [0.035 * lado('patilla derecha'), 0.004, -0.06],
        }
        # 0-0,8 montadas · 0,8-2,2 se separan · 2,2-4,2 despiece · 4,2-5,8 encajan · 5,8-7 montadas
        tiempos = np.array([0, 0.8, 2.2, 4.2, 5.8, 7.0], np.float32)
        peso = np.array([0, 0, 1, 1, 0, 0], np.float32)
        # «encuadre»: un triángulo degenerado (invisible) que llega a las esquinas del
        # despiece, para que el visor encuadre también las piezas separadas
        ext = np.vstack([np.vstack([p + np.array(despiece[n]) for n, (p, _, _) in piezas.items()]), todo])
        bmin, bmax = ext.min(0), ext.max(0)
        ep = np.array([bmin, bmax, bmax], np.float32)
        en = np.tile(np.float32([0, 1, 0]), (3, 1))
        prim = G.Primitive(attributes=G.Attributes(POSITION=accesor(ep, 'VEC3', G.ARRAY_BUFFER, True),
                                                   NORMAL=accesor(en, 'VEC3', G.ARRAY_BUFFER),
                                                   TEXCOORD_0=accesor(np.zeros((3, 2), np.float32), 'VEC2', G.ARRAY_BUFFER)),
                           indices=accesor(np.arange(3, dtype=np.uint32), 'SCALAR', G.ELEMENT_ARRAY_BUFFER), material=0)
        gltf.meshes.append(G.Mesh(name='encuadre', primitives=[prim]))
        gltf.nodes.append(G.Node(name='encuadre', mesh=len(gltf.meshes) - 1))
        encuadre = len(gltf.nodes) - 1
        canales, muestreadores = [], []
        for i, nombre in enumerate(piezas):
            d = np.array(despiece[nombre], np.float32)
            valores = (peso[:, None] * d[None]).astype(np.float32)
            muestreadores.append(G.AnimationSampler(input=accesor(tiempos, 'SCALAR', minmax=True),
                                                    output=accesor(valores, 'VEC3'), interpolation='LINEAR'))
            canales.append(G.AnimationChannel(sampler=len(muestreadores) - 1, target=G.AnimationChannelTarget(node=hijos[i], path='translation')))
        gltf.animations.append(G.Animation(name='Montaje', channels=canales, samplers=muestreadores))
        # tramos suavizados: más fotogramas clave con una curva de aceleración
        suavizar(gltf, datos)

    gltf.scenes.append(G.Scene(nodes=hijos + ([encuadre] if animar else [])))
    gltf.scene = 0
    gltf.buffers.append(G.Buffer(byteLength=len(datos)))
    gltf.set_binary_blob(bytes(datos))
    return gltf


def suavizar(gltf, datos):
    """Rehace las pistas con 60 claves por tramo y una curva suave (ease in-out)."""
    blob = bytes(datos)
    for s in gltf.animations[0].samplers:
        ai, ao = gltf.accessors[s.input], gltf.accessors[s.output]
        t = np.frombuffer(blob, np.float32, ai.count, gltf.bufferViews[ai.bufferView].byteOffset)
        v = np.frombuffer(blob, np.float32, ao.count * 3, gltf.bufferViews[ao.bufferView].byteOffset).reshape(-1, 3)
        tn, vn = [], []
        for k in range(len(t) - 1):
            u = np.linspace(0, 1, 30, endpoint=False)
            e = u * u * (3 - 2 * u)
            tn.append(t[k] + (t[k + 1] - t[k]) * u)
            vn.append(v[k] + (v[k + 1] - v[k]) * e[:, None])
        tn.append(t[-1:]); vn.append(v[-1:])
        tn = np.concatenate(tn).astype(np.float32); vn = np.concatenate(vn).astype(np.float32)
        for arr, acc in ((tn, ai), (vn, ao)):
            while len(datos) % 4:
                datos.append(0)
            b = arr.tobytes()
            gltf.bufferViews.append(G.BufferView(buffer=0, byteOffset=len(datos), byteLength=len(b)))
            datos.extend(b)
            acc.bufferView = len(gltf.bufferViews) - 1
            acc.count = len(arr)
        ai.min, ai.max = [float(tn.min())], [float(tn.max())]


os.makedirs(SALIDA, exist_ok=True)
for nombre, animar in (('ovum-g1.glb', False), ('ovum-g1-montaje.glb', True)):
    ruta = os.path.join(SALIDA, nombre)
    construir(animar).save_binary(ruta)
    print(ruta, f'{os.path.getsize(ruta) / 1e6:.1f} MB')
