"""Modelo 3D del Kuris para la web.

Uso: python3 herramientas/kuris_modelo.py <dronreal1.glb> [salida.glb]

Parte del .glb que Martín exportó de 3ds Max (versión blanca de la tienda
MON Drones) y le pone los materiales de los renders finales: carcasa de metal
bronce oscuro brillante, ojo de LED verde, bases de las ruedas casi negras y
ruedas de goma. Los colores base van en espacio lineal.
"""
import sys

import pygltflib

ENTRADA = sys.argv[1]
SALIDA = sys.argv[2] if len(sys.argv) > 2 else 'public/modelos/kuris.glb'


def lineal(r, g, b):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return [c(r), c(g), c(b), 1.0]


# nombre del material en 3ds Max -> (color sRGB, metálico, rugosidad)
MATERIALES = {
    'plastico': ((66, 54, 40), 1.0, 0.24),            # cabeza
    'plastico_patas': ((66, 54, 40), 1.0, 0.26),     # brazos y anillo
    'Material__25': ((48, 40, 30), 1.0, 0.3),         # disco inferior
    'plastico_bases_ruedas': ((22, 20, 17), 0.3, 0.45),
    'goma_ruedas': ((14, 14, 14), 0.0, 0.7),
}

g = pygltflib.GLTF2().load(ENTRADA)
for m in g.materials:
    pbr = m.pbrMetallicRoughness
    m.extensions = {}
    if m.name in MATERIALES:
        rgb, metal, rug = MATERIALES[m.name]
        pbr.baseColorFactor = lineal(*rgb)
        pbr.metallicFactor = metal
        pbr.roughnessFactor = rug
        m.emissiveFactor = [0.0, 0.0, 0.0]
    elif m.name == 'led_ojos':
        pbr.baseColorFactor = lineal(20, 60, 20)
        pbr.metallicFactor = 0.0
        pbr.roughnessFactor = 0.3
        m.emissiveFactor = [0.12, 1.0, 0.1]
        m.extensions = {'KHR_materials_emissive_strength': {'emissiveStrength': 2.5}}
    m.name = {'plastico': 'carcasa', 'plastico_patas': 'brazos', 'Material__25': 'disco',
              'plastico_bases_ruedas': 'bases_ruedas', 'goma_ruedas': 'ruedas',
              'led_ojos': 'led_verde'}.get(m.name, m.name)

# Gira el dron para que el ojo mire casi a la cámara inicial del visor (32°):
# el frente queda a 10° y se ve de tres cuartos.
import math
a = math.radians(-80)
raiz = pygltflib.Node(name='Kuris', children=list(g.scenes[0].nodes),
                      rotation=[0.0, math.sin(a / 2), 0.0, math.cos(a / 2)])
g.nodes.append(raiz)
g.scenes[0].nodes = [len(g.nodes) - 1]

g.extensionsUsed = ['KHR_materials_emissive_strength']
g.extensionsRequired = []
g.save_binary(SALIDA)

# 3ds Max dejó el dron lejos del origen: lo centra y lo apoya en el suelo
# para que el visor gire alrededor de él.
import trimesh
lo, hi = trimesh.load(SALIDA).bounds
raiz.translation = [-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2]
g.save_binary(SALIDA)
print('Guardado', SALIDA)
