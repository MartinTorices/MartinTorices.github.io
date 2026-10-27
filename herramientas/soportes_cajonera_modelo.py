"""Modelos 3D de los soportes de cajonera para el visor de la web.

Parte de los dos STL que exporta Martín desde SolidWorks (Barra.STL y Tapa.STL).
SolidWorks los guarda desplazados al espacio positivo, así que aquí se devuelven
a las coordenadas de cada pieza:
- Barra: caja de pieza X −118…118, Y 0…18, Z −8…8 mm (en el STL, +118, 0, +8).
- Tapa: caja de pieza X −5…5, Y −5…5, Z −10…0 mm (en el STL, +5, +5, +10). Como en
  «Barras Armario.SLDASM», su eje Z va según el Y de la barra, con el origen 20 mm
  por encima de la base: el vástago entra en el tetón y la cabeza queda encima.
  Lleva una tapa en cada uno de los tres tetones (x = −110, 0 y 110 mm).
Material: PLA gris grafito mate (impreso en una Bambu Lab). Aristas vivas
conservadas (normales separadas a más de 30°).

Crea:
- soportes-cajonera.glb: montado.
- soportes-cajonera-despiece.glb: despiece en bucle de 6 s; las tapas suben 24 mm,
  una detrás de otra, y vuelven a encajar. Lleva un triángulo degenerado
  («encuadre») para que el visor encuadre también las tapas levantadas.

Uso: python3 herramientas/soportes_cajonera_modelo.py <Barra.STL> <Tapa.STL> [carpeta de salida]
"""
import os
import sys
import numpy as np
import pygltflib as G
import trimesh

BARRA, TAPA = sys.argv[1], sys.argv[2]
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SALIDA = sys.argv[3] if len(sys.argv) > 3 else os.path.join(RAIZ, 'public', 'modelos')
TETONES = (-110.0, 0.0, 110.0)  # mm, centros de los tetones en X
SUBIDA = 0.024                    # m, cuánto suben las tapas en el despiece


def preparar(m):
    m = trimesh.graph.smooth_shade(m, angle=np.radians(30))
    return np.asarray(m.vertices, np.float32), np.asarray(m.vertex_normals, np.float32), np.asarray(m.faces, np.uint32)


barra = trimesh.load(BARRA)
barra.apply_translation([-118, 0, -8])
tapa0 = trimesh.load(TAPA)
tapa0.apply_translation([-5, -5, -10])
# eje Z de la tapa → +Y de la barra (pieza de revolución: el giro alrededor del eje no importa)
R = np.eye(4)
R[:3, :3] = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]
tapa0.apply_transform(R)
tapa0.apply_translation([0, 20, 0])

piezas = {'barra': barra}
for i, x in enumerate(TETONES):
    t = tapa0.copy()
    t.apply_translation([x, 0, 0])
    piezas[f'tapa_{i + 1}'] = t

# mm → m, apoyado en Y = 0 y centrado en X y Z
todo = np.vstack([m.vertices for m in piezas.values()])
base = np.array([(todo[:, 0].min() + todo[:, 0].max()) / 2, todo[:, 1].min(), (todo[:, 2].min() + todo[:, 2].max()) / 2])
for m in piezas.values():
    m.apply_translation(-base)
    m.apply_scale(0.001)
datos_piezas = {n: preparar(m) for n, m in piezas.items()}


def construir(animar):
    gltf = G.GLTF2(asset=G.Asset(generator='soportes_cajonera_modelo.py'))
    datos = bytearray()

    def accesor(arr, tipo, objetivo=None, minmax=False):
        while len(datos) % 4:
            datos.append(0)
        b = arr.tobytes()
        gltf.bufferViews.append(G.BufferView(buffer=0, byteOffset=len(datos), byteLength=len(b), target=objetivo))
        datos.extend(b)
        comp = G.UNSIGNED_INT if arr.dtype == np.uint32 else G.FLOAT
        a = G.Accessor(bufferView=len(gltf.bufferViews) - 1, componentType=comp, count=len(arr), type=tipo)
        if minmax:
            a.min = arr.min(0).tolist() if arr.ndim > 1 else [float(arr.min())]
            a.max = arr.max(0).tolist() if arr.ndim > 1 else [float(arr.max())]
        gltf.accessors.append(a)
        return len(gltf.accessors) - 1

    gltf.materials.append(G.Material(
        name='PLA grafito',
        pbrMetallicRoughness=G.PbrMetallicRoughness(baseColorFactor=[0.055, 0.058, 0.062, 1.0], metallicFactor=0.0, roughnessFactor=0.55)))

    def malla(nombre, p, n, f):
        prim = G.Primitive(attributes=G.Attributes(POSITION=accesor(p, 'VEC3', G.ARRAY_BUFFER, True),
                                                   NORMAL=accesor(n, 'VEC3', G.ARRAY_BUFFER)),
                           indices=accesor(f.ravel(), 'SCALAR', G.ELEMENT_ARRAY_BUFFER), material=0)
        gltf.meshes.append(G.Mesh(name=nombre, primitives=[prim]))
        gltf.nodes.append(G.Node(name=nombre, mesh=len(gltf.meshes) - 1))
        return len(gltf.nodes) - 1

    nodos = {n: malla(n, *d) for n, d in datos_piezas.items()}
    escena = list(nodos.values())

    if animar:
        # encuadre: llega hasta las tapas levantadas
        bmin = np.vstack([d[0] for d in datos_piezas.values()]).min(0)
        bmax = np.vstack([d[0] for d in datos_piezas.values()]).max(0) + [0, SUBIDA, 0]
        ep = np.array([bmin, bmax, bmax], np.float32)
        escena.append(malla('encuadre', ep, np.tile(np.float32([0, 1, 0]), (3, 1)), np.arange(3, dtype=np.uint32)))

        # 6 s en bucle: cada tapa sube 1 s, espera arriba y baja 1 s; la segunda y la
        # tercera empiezan 0,2 y 0,4 s más tarde. Curva suave (ease in-out).
        canales, muestreadores = [], []
        t = np.round(np.arange(0, 6.0001, 1 / 30), 4).astype(np.float32)
        suave = lambda u: np.clip(u, 0, 1) ** 2 * (3 - 2 * np.clip(u, 0, 1))
        for i in range(len(TETONES)):
            r = 0.2 * i
            h = suave((t - 0.6 - r) / 1.0) - suave((t - 3.6 - r) / 1.0)
            valores = np.zeros((len(t), 3), np.float32)
            valores[:, 1] = SUBIDA * h
            muestreadores.append(G.AnimationSampler(input=accesor(t, 'SCALAR', minmax=True),
                                                    output=accesor(valores, 'VEC3'), interpolation='LINEAR'))
            canales.append(G.AnimationChannel(sampler=len(muestreadores) - 1,
                                              target=G.AnimationChannelTarget(node=nodos[f'tapa_{i + 1}'], path='translation')))
        gltf.animations.append(G.Animation(name='Despiece', channels=canales, samplers=muestreadores))

    gltf.scenes.append(G.Scene(nodes=escena))
    gltf.scene = 0
    gltf.buffers.append(G.Buffer(byteLength=len(datos)))
    gltf.set_binary_blob(bytes(datos))
    return gltf


os.makedirs(SALIDA, exist_ok=True)
for nombre, animar in (('soportes-cajonera.glb', False), ('soportes-cajonera-despiece.glb', True)):
    ruta = os.path.join(SALIDA, nombre)
    construir(animar).save_binary(ruta)
    print(ruta, f'{os.path.getsize(ruta) / 1e3:.0f} kB')
print('tamaño montado (mm):', ((todo.max(0) - todo.min(0))).round(1))
