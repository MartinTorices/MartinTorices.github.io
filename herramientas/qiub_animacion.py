"""Dosificador QIUB en funcionamiento: modelo 3D animado para el visor.

Parte de public/modelos/dosificador-qiub.glb (bote, tapa y tornillo, de pie y en
metros; lo genera herramientas/qiub_modelo.py) y crea dosificador-qiub-uso.glb con
una animación en bucle de 9 s:

  0,0-0,6 s  el bote está de pie junto a un cuenco
  0,6-1,8 s  se levanta y se vuelca sobre el cuenco (160°, salida hacia abajo)
  2,2 / 3,4 / 4,6 s  tres clics: la ruleta gira 120° cada vez y cae una dosis
             de pimentón (unos 1,14 ml por clic); el montón del cuenco crece
  6,0-7,2 s  el bote vuelve a su sitio
  8,6-9,0 s  el montón se recoge para empezar otra vez

Uso: python3 herramientas/qiub_animacion.py [public/modelos/dosificador-qiub.glb] [salida.glb]
"""
import os
import sys
import numpy as np
import trimesh
import pygltflib as G

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ORIGEN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'public', 'modelos', 'dosificador-qiub.glb')
SALIDA = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, 'public', 'modelos', 'dosificador-qiub-uso.glb')
rng = np.random.default_rng(7)

DURACION = 9.0
CLICS = [2.2, 3.4, 4.6]          # inicio de cada clic (s)
GIRO = 0.4                        # duración del giro de 120° (s)
CAIDA = 0.5                       # tiempo de caída de cada grano (cámara lenta)
POR_CLIC = 45                     # granos visibles por dosis (un chorro fino)
VUELCO = np.radians(160)          # inclinación de uso
ALTURA_SALIDA = 0.13              # m, altura de la salida sobre la mesa al dosificar
SEPARACION = 0.10                 # m, el bote de pie a la izquierda del cuenco
# la cámara inicial del visor está a 32° (camera-orbit="32deg 72deg auto"): el bote
# se coloca a su izquierda y se vuelca en el plano de la imagen, para verlo de perfil
THETA = np.radians(32)
DERECHA = np.array([np.cos(THETA), 0, -np.sin(THETA)])
HACIA_CAMARA = np.array([np.sin(THETA), 0, np.cos(THETA)])

# ── Piezas del modelo estático ───────────────────────────────────────────────
escena = trimesh.load(ORIGEN, process=False)
piezas = {}
for nodo in escena.graph.nodes_geometry:
    T, g = escena.graph[nodo]
    m = escena.geometry[g].copy()
    m.apply_transform(T)
    piezas[g] = m
bote, tapa, tornillo = piezas['bote'], piezas['tapa'], piezas['tornillo']
mats_origen = {k: v.visual.material for k, v in piezas.items()}

todo = np.vstack([p.vertices for p in piezas.values()])
lo, hi = todo.min(0), todo.max(0)
P0 = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2])  # centro del conjunto

# salida del producto: centro de la cara superior de la tapa (agujero de la planta)
sup = tapa.vertices[tapa.vertices[:, 1] > tapa.vertices[:, 1].max() - 0.0015]
salida_local = np.array([(sup[:, 0].min() + sup[:, 0].max()) / 2, hi[1], (sup[:, 2].min() + sup[:, 2].max()) / 2])

# eje del tornillo (componente principal) y su centro
c_t = tornillo.vertices.mean(0)
eje_t = np.linalg.svd(tornillo.vertices - c_t, full_matrices=False)[2][0]


# ── Utilidades de cuaterniones (x, y, z, w como pide glTF) ───────────────────
def quat(eje, ang):
    eje = np.asarray(eje, float) / np.linalg.norm(eje)
    s = np.sin(ang / 2)
    return np.array([*(eje * s), np.cos(ang / 2)])


def rotar(q, v):
    x, y, z, w = q
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    return R @ v


def suave(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


# ── Poses del conjunto (nodo que gira alrededor de su centro P0) ─────────────
q_reposo = np.array([0, 0, 0, 1.0])
q_uso = quat(HACIA_CAMARA, -VUELCO)  # la tapa gira hacia el cuenco
t_reposo = -SEPARACION * DERECHA + np.array([0, P0[1] - lo[1], 0.0])  # de pie sobre la mesa (y = 0)
salida_rel = salida_local - P0
s_uso = rotar(q_uso, salida_rel)
t_uso = np.array([-s_uso[0], ALTURA_SALIDA - s_uso[1], -s_uso[2]])  # salida justo encima del cuenco
salida_mundo = t_uso + s_uso


def pose(t):
    """Traslación y giro del conjunto en el instante t."""
    if t <= 0.6 or t >= 7.2:
        u = 0.0
    elif t < 1.8:
        u = suave((t - 0.6) / 1.2)
    elif t <= 6.0:
        u = 1.0
    else:
        u = 1 - suave((t - 6.0) / 1.2)
    # arco: sube un poco al moverse para no rozar el cuenco
    tr = (1 - u) * t_reposo + u * t_uso + np.array([0, 0.04 * np.sin(np.pi * u), 0])
    q = trimesh.transformations.quaternion_slerp(
        [1, 0, 0, 0], [q_uso[3], *q_uso[:3]], u)  # (w, x, y, z)
    return tr, np.array([q[1], q[2], q[3], q[0]])


# ── Geometría nueva: cuenco, montón y granos ─────────────────────────────────
def torno(perfil, n=96):
    """Sólido de revolución alrededor de Y a partir de un perfil (r, y) cerrado."""
    perfil = np.asarray(perfil, float)
    k = len(perfil)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    v = np.array([[r * np.cos(a), y, r * np.sin(a)] for a in ang for r, y in perfil])
    f = []
    for i in range(n):
        j = (i + 1) % n
        for p in range(k - 1):
            a, b = i * k + p, i * k + p + 1
            c, d = j * k + p, j * k + p + 1
            f += [[a, c, b], [b, c, d]]
    m = trimesh.Trimesh(v, f, process=True)
    m.fix_normals()
    return m


R_CUENCO, H_CUENCO, E = 0.048, 0.032, 0.003
cuenco = torno([(0.0, 0.0), (0.030, 0.0), (R_CUENCO, H_CUENCO), (R_CUENCO - E, H_CUENCO),
                (0.028, E), (0.0, E)])
FONDO = E
monton = torno([(0.0, 0.0), (0.030, 0.0), (0.022, 0.004), (0.010, 0.010), (0.0, 0.012)], n=64)
grano = trimesh.creation.icosphere(subdivisions=1, radius=1.0)

# ── glTF a mano ──────────────────────────────────────────────────────────────
gltf = G.GLTF2(scene=0, scenes=[G.Scene(nodes=[])], asset=G.Asset(generator='qiub_animacion.py'))
blob = bytearray()


def vista(datos, objetivo=None):
    global blob
    while len(blob) % 4:
        blob += b'\0'
    off = len(blob)
    blob += datos
    gltf.bufferViews.append(G.BufferView(buffer=0, byteOffset=off, byteLength=len(datos), target=objetivo))
    return len(gltf.bufferViews) - 1


def accesor(arr, tipo, objetivo=None, minmax=False):
    arr = np.ascontiguousarray(arr)
    comp = G.UNSIGNED_INT if arr.dtype == np.uint32 else G.FLOAT
    acc = G.Accessor(bufferView=vista(arr.tobytes(), objetivo), componentType=comp,
                     count=len(arr), type=tipo)
    if minmax:
        a2 = arr.reshape(len(arr), -1)
        acc.min = a2.min(0).tolist()
        acc.max = a2.max(0).tolist()
    gltf.accessors.append(acc)
    return len(gltf.accessors) - 1


def material(nombre, color, alfa=1.0, rugosidad=0.5, blend=False, emisivo=None):
    m = G.Material(name=nombre, doubleSided=False,
                   pbrMetallicRoughness=G.PbrMetallicRoughness(
                       baseColorFactor=[*color, alfa], metallicFactor=0.0, roughnessFactor=rugosidad),
                   alphaMode='BLEND' if blend else 'OPAQUE')
    if emisivo:
        m.emissiveFactor = emisivo
    gltf.materials.append(m)
    return len(gltf.materials) - 1


def malla(m, mat, nombre, desplazar=np.zeros(3)):
    v = (m.vertices - desplazar).astype(np.float32)
    n = np.asarray(m.vertex_normals, np.float32)
    f = np.asarray(m.faces, np.uint32).reshape(-1)
    prim = G.Primitive(attributes=G.Attributes(POSITION=accesor(v, G.VEC3, G.ARRAY_BUFFER, True),
                                               NORMAL=accesor(n, G.VEC3, G.ARRAY_BUFFER)),
                       indices=accesor(f, G.SCALAR, G.ELEMENT_ARRAY_BUFFER), material=mat)
    gltf.meshes.append(G.Mesh(name=nombre, primitives=[prim]))
    return len(gltf.meshes) - 1


def nodo(nombre, malla_i=None, hijos=None, t=None, r=None, s=None):
    nd = G.Node(name=nombre)
    if malla_i is not None:
        nd.mesh = malla_i
    if hijos:
        nd.children = hijos
    if t is not None:
        nd.translation = [float(x) for x in t]
    if r is not None:
        nd.rotation = [float(x) for x in r]
    if s is not None:
        nd.scale = [float(x) for x in s]
    gltf.nodes.append(nd)
    return len(gltf.nodes) - 1


def mat_de(nombre):
    m = mats_origen[nombre]
    col = list(np.asarray(m.baseColorFactor, float).reshape(-1)[:4])
    if max(col) > 1.0:
        col = [c / 255 for c in col]
    return material(m.name or nombre, col[:3], col[3], float(m.roughnessFactor or 0.3), blend=col[3] < 1)


m_bote, m_tapa, m_torn = mat_de('bote'), mat_de('tapa'), mat_de('tornillo')
m_cuenco = material('Cerámica antracita', [0.035, 0.035, 0.038], 1.0, 0.45)
m_polvo = material('Pimentón', [0.42, 0.065, 0.018], 1.0, 0.95)

# conjunto: bote y tapa colgando de un nodo que gira alrededor de su centro;
# el tornillo, de otro nodo en su eje que gira 120° por clic
n_bote = nodo('bote', malla(bote, m_bote, 'bote', P0))
n_tapa = nodo('tapa', malla(tapa, m_tapa, 'tapa', P0))
n_torn_m = nodo('tornillo_malla', malla(tornillo, m_torn, 'tornillo', c_t))
n_torn = nodo('tornillo', hijos=[n_torn_m], t=c_t - P0)
# orden de dibujo: primero lo de dentro (tornillo), luego tapa y bote
n_conj = nodo('conjunto', hijos=[n_torn, n_tapa, n_bote], t=t_reposo, r=q_reposo)

n_cuenco = nodo('cuenco', malla(cuenco, m_cuenco, 'cuenco'))
i_monton = malla(monton, m_polvo, 'monton')
n_monton = nodo('monton', i_monton, t=[0, FONDO, 0], s=[0, 0, 0])
i_grano = malla(grano, m_polvo, 'grano')

# centinela: triángulo degenerado en el punto más alto del recorrido, para que el
# visor encuadre también el bote volcado (model-viewer encuadra la pose inicial)
alto = max(t_uso[1] + np.abs(rotar(q_uso, todo.T - P0[:, None]).T)[:, 1].max(), hi[1] - lo[1]) + 0.01
cent = trimesh.Trimesh([[0, alto, 0]] * 3 + [list(-(SEPARACION + 0.03) * DERECHA)] * 3, [[0, 1, 2], [3, 4, 5]], process=False)
cent.vertex_normals = np.tile([0, 1, 0], (6, 1))
n_cent = nodo('encuadre', malla(cent, m_cuenco, 'encuadre'))

raiz = [n_conj, n_cuenco, n_monton, n_cent]

# ── Animación ────────────────────────────────────────────────────────────────
canales, muestreadores = [], []


def pista(nodo_i, ruta, tiempos, valores, interp='LINEAR'):
    tiempos = np.asarray(tiempos, np.float32)
    valores = np.asarray(valores, np.float32)
    ti = accesor(tiempos, G.SCALAR, minmax=True)
    vi = accesor(valores, G.VEC4 if ruta == 'rotation' else G.VEC3)
    muestreadores.append(G.AnimationSampler(input=ti, output=vi, interpolation=interp))
    canales.append(G.AnimationChannel(sampler=len(muestreadores) - 1,
                                      target=G.AnimationChannelTarget(node=nodo_i, path=ruta)))


# conjunto: muestreado cada 1/30 s para que el arco y la aceleración queden suaves
ts = np.round(np.arange(0, DURACION + 1e-6, 1 / 30), 4)
poses = [pose(t) for t in ts]
pista(n_conj, 'translation', ts, [p[0] for p in poses])
pista(n_conj, 'rotation', ts, [p[1] for p in poses])

# tornillo: 0° → 120° → 240° → 360°, cada giro con arranque y frenado suaves
tt, qq = [0.0], [quat(eje_t, 0)]
for k, c in enumerate(CLICS):
    for u in np.linspace(0, 1, 9):
        tt.append(c + u * GIRO)
        qq.append(quat(eje_t, np.radians(120) * (k + suave(u))))
tt.append(DURACION)
qq.append(qq[-1])
pista(n_torn, 'rotation', tt, qq)

# granos: salen de la boca durante el giro y caen con aceleración hasta el montón
alt_monton = [0.0, 0.006, 0.009, 0.012]
for k, c in enumerate(CLICS):
    for g in range(POR_CLIC):
        t0 = c + 0.05 + (GIRO + 0.1) * g / POR_CLIC + rng.uniform(-0.01, 0.01)
        r = rng.uniform(0.00045, 0.0009)
        x0 = salida_mundo + np.array([rng.normal(0, 0.0015), 0, rng.normal(0, 0.0015)])
        ang = rng.uniform(0, 2 * np.pi)
        dr = 0.014 * np.sqrt(rng.uniform(0, 1))
        x1 = np.array([dr * np.cos(ang), FONDO + alt_monton[k + 1] * (1 - dr / 0.03), dr * np.sin(ang)])
        n_g = nodo(f'grano_{k}_{g}', i_grano, t=x0, s=[0, 0, 0])
        raiz.append(n_g)
        us = np.linspace(0, 1, 7)
        tiempos = [0.0] + list(t0 + us * CAIDA) + [DURACION]
        pos = [x0] + [x0 + (x1 - x0) * np.array([u, u * u, u]) for u in us] + [x1]
        pista(n_g, 'translation', tiempos, pos)
        pista(n_g, 'scale', [0.0, t0, t0 + CAIDA + 0.02],
              [[0, 0, 0], [r, r * rng.uniform(0.8, 1.2), r], [0, 0, 0]], interp='STEP')

# montón: crece un escalón por dosis y se recoge al final del ciclo
tm = [0.0]
sm = [[0, 0, 0]]
for k, c in enumerate(CLICS):
    a, b = c + 0.35, c + GIRO + CAIDA + 0.15
    f = [0.0, 0.55, 0.8, 1.0]
    tm += [a, b]
    sm += [[f[k]] * 3, [f[k + 1]] * 3]
tm += [8.6, DURACION]
sm += [[1, 1, 1], [0, 0, 0]]
pista(n_monton, 'scale', tm, sm)

gltf.animations.append(G.Animation(name='Dosificar', channels=canales, samplers=muestreadores))
gltf.scenes[0].nodes = raiz
gltf.buffers.append(G.Buffer(byteLength=len(blob)))
gltf.set_binary_blob(bytes(blob))
gltf.save_binary(SALIDA)
print(SALIDA, f'{os.path.getsize(SALIDA) / 1e6:.1f} MB',
      '| salida en', (salida_mundo * 1000).round(1), 'mm | eje tornillo', eje_t.round(2))
