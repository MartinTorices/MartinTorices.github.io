"""Modelo 3D del dosificador QIUB para el visor de la web.

Parte del .obj que exporta Martín desde Blender (tres objetos: bote, tapa y tornillo),
lo pone de pie (eje del bote en Y, tapa arriba), lo escala a su tamaño real
(142 mm de alto, como en el plano) y le da materiales de plástico translúcido:
- bote: PET transparente, casi incoloro
- tapa: rPET esmerilado con un toque rosado, como en los renders
- tornillo: el mismo rPET, algo más opaco para que el mecanismo se lea dentro de la tapa

Uso: python3 herramientas/qiub_modelo.py <qiubcompleto.obj> [public/modelos/dosificador-qiub.glb]
"""
import os
import sys
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

ORIGEN = sys.argv[1]
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SALIDA = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, 'public', 'modelos', 'dosificador-qiub.glb')
ALTO = 0.142  # m, cota total del plano del conjunto

escena = trimesh.load(ORIGEN, split_object=True, group_material=False, process=False, maintain_order=True)
piezas = sorted(escena.geometry.values(), key=lambda g: -len(g.vertices))
# por tamaño: el bote es la pieza más larga, luego la tapa y el tornillo
piezas = sorted(piezas, key=lambda g: -np.ptp(g.vertices, axis=0).max())
bote, tapa, tornillo = piezas[0], piezas[1], piezas[2]

# eje del bote (componente principal) orientado hacia la tapa
c = bote.vertices - bote.vertices.mean(0)
eje = np.linalg.svd(c[::5], full_matrices=False)[2][0]
if np.dot(tapa.vertices.mean(0) - bote.vertices.mean(0), eje) < 0:
    eje = -eje
R = trimesh.geometry.align_vectors(eje, [0, 1, 0])

# la ruleta del tornillo mirando a la cámara (+Z): giro alrededor de Y
todo = np.vstack([p.vertices for p in piezas])
todo_r = trimesh.transform_points(todo, R)
centro = todo_r.mean(0)
ruleta = trimesh.transform_points(tornillo.vertices, R)
ruleta = ruleta[np.argsort(-ruleta[:, 1])][: len(ruleta) // 4].mean(0)  # parte alta del tornillo
d = ruleta - centro
ang = np.arctan2(d[0], d[2])
Ry = trimesh.transformations.rotation_matrix(-ang + np.radians(35), [0, 1, 0])
T = Ry @ R

pts = trimesh.transform_points(todo, T)
escala = ALTO / np.ptp(pts[:, 1])
base = np.array([(pts[:, 0].min() + pts[:, 0].max()) / 2, pts[:, 1].min(), (pts[:, 2].min() + pts[:, 2].max()) / 2])
S = trimesh.transformations.scale_matrix(escala) @ trimesh.transformations.translation_matrix(-base)
M = S @ T


def material(nombre, color, alfa, rugosidad):
    return PBRMaterial(name=nombre, baseColorFactor=[*color, alfa], metallicFactor=0.0,
                       roughnessFactor=rugosidad, alphaMode='BLEND', doubleSided=False)


mats = {
    # baseColorFactor en espacio lineal; tonos algo oscuros para que el plástico
    # translúcido no se pierda sobre el fondo claro del visor
    'bote': material('PET transparente', [0.30, 0.33, 0.35], 0.35, 0.06),
    'tapa': material('rPET esmerilado', [0.48, 0.41, 0.45], 0.62, 0.28),
    'tornillo': material('rPET tornillo', [0.38, 0.29, 0.34], 0.95, 0.30),
}

salida = trimesh.Scene()
for nombre, pieza in (('bote', bote), ('tapa', tapa), ('tornillo', tornillo)):
    m = trimesh.Trimesh(vertices=pieza.vertices.copy(), faces=pieza.faces.copy(), process=False)
    n = getattr(pieza, 'vertex_normals', None)
    m.apply_transform(M)
    if n is not None and len(n) == len(pieza.vertices):
        m.vertex_normals = (T[:3, :3] @ np.asarray(n).T).T  # solo giro: las normales del .obj se conservan
    m.visual = trimesh.visual.TextureVisuals(material=mats[nombre])
    salida.add_geometry(m, node_name=nombre, geom_name=nombre)

os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
salida.export(SALIDA)
print(SALIDA, f'{os.path.getsize(SALIDA) / 1e6:.1f} MB', 'tamaño (mm):', (salida.extents * 1000).round(1))
