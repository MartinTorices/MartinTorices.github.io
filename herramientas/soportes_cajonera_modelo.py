"""Modelo 3D de los soportes de cajonera para el visor de la web.

Parte de los dos STL que exporta Martín desde SolidWorks (Barra.STL y Tapa.STL).
SolidWorks los guarda desplazados al espacio positivo, así que aquí se devuelven
a las coordenadas de cada pieza y se colocan como en «Barras Armario.SLDASM»:
- Barra: caja de pieza X −118…118, Y 0…18, Z −8…8 mm (en el STL, +118, 0, +8).
- Tapa: caja de pieza X −5…5, Y −5…5, Z −10…0 mm (en el STL, +5, +5, +10). En el
  ensamblaje, su eje Z va según el Y de la barra, con el origen en (−110, 20, 0) mm
  de la barra: el vástago entra en la horquilla del extremo y la cabeza queda encima.
Material: PLA gris grafito mate (impreso en una Bambu Lab).
Las aristas vivas se conservan (normales separadas a más de 30°).

Uso: python3 herramientas/soportes_cajonera_modelo.py <Barra.STL> <Tapa.STL> [public/modelos/soportes-cajonera.glb]
"""
import os
import sys
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

BARRA, TAPA = sys.argv[1], sys.argv[2]
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SALIDA = sys.argv[3] if len(sys.argv) > 3 else os.path.join(RAIZ, 'public', 'modelos', 'soportes-cajonera.glb')

barra = trimesh.load(BARRA)
barra.apply_translation([-118, 0, -8])

tapa = trimesh.load(TAPA)
tapa.apply_translation([-5, -5, -10])
# giro del ensamblaje (convenio fila de SolidWorks: p_asm = p·R + T), sin la parte en X
# que no importa por ser una pieza de revolución: el eje Z de la tapa pasa a ser +Y
R = np.array([[-0.84052, 0, 0.54177], [0.54177, 0, 0.84052], [0, 1, 0]])
M = np.eye(4)
M[:3, :3] = R.T
M[:3, 3] = [-110.0, 20.0, 0.0]
tapa.apply_transform(M)

# mm → m, apoyado en Y = 0 y centrado en X y Z
todo = np.vstack([barra.vertices, tapa.vertices])
base = np.array([(todo[:, 0].min() + todo[:, 0].max()) / 2, todo[:, 1].min(), (todo[:, 2].min() + todo[:, 2].max()) / 2])

pla = PBRMaterial(name='PLA grafito', baseColorFactor=[0.055, 0.058, 0.062, 1.0],
                  metallicFactor=0.0, roughnessFactor=0.55)

escena = trimesh.Scene()
for nombre, m in (('barra', barra), ('tapa', tapa)):
    m.apply_translation(-base)
    m.apply_scale(0.001)
    m = trimesh.graph.smooth_shade(m, angle=np.radians(30))
    m.visual = trimesh.visual.TextureVisuals(material=pla)
    escena.add_geometry(m, node_name=nombre, geom_name=nombre)

os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
escena.export(SALIDA)
print(SALIDA, f'{os.path.getsize(SALIDA) / 1e3:.0f} kB', 'tamaño (mm):', (escena.extents * 1000).round(1))
