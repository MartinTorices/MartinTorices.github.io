// Vista «Por partes» de los soportes de cajonera: a partir del modelo montado
// (public/modelos/soportes-cajonera.glb, de soportes_cajonera_modelo.py) crea
// public/modelos/soportes-cajonera-despiece.glb con una animación en bucle de 7 s:
// las tres tapas suben 32 mm sobre sus tetones (una detrás de otra), se quedan
// arriba para ver el vástago y el tetón hueco, y vuelven a encajar.
//
// Uso: node herramientas/soportes_cajonera_despiece.mjs [entrada.glb] [salida.glb]
import { NodeIO, VertexLayout } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';

const entrada = process.argv[2] ?? 'public/modelos/soportes-cajonera.glb';
const salida = process.argv[3] ?? 'public/modelos/soportes-cajonera-despiece.glb';
const SUBIDA = 0.032; // m
const CICLO = 7; // s
const RETRASO = 0.18; // s entre una tapa y la siguiente

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).setVertexLayout(VertexLayout.SEPARATE);
const doc = await io.read(entrada);
const raiz = doc.getRoot();
const buffer = raiz.listBuffers()[0];
const anim = doc.createAnimation('despiece');

// curva suave (ease in-out) muestreada: abajo → arriba → abajo
const suave = (t) => t * t * (3 - 2 * t);
const tapas = raiz.listNodes().filter((n) => n.getName().startsWith('tapa_')).sort((a, b) => a.getName().localeCompare(b.getName()));
if (tapas.length === 0) throw new Error('No hay nodos «tapa_*» en ' + entrada);

tapas.forEach((nodo, k) => {
  const t0 = 0.6 + k * RETRASO; // empieza a subir
  const subir = 1.1; // duración de la subida
  const arriba = 2.6; // tiempo arriba
  const bajar = 1.1;
  const tiempos = [];
  const valores = [];
  const base = nodo.getTranslation();
  const pon = (t, h) => { tiempos.push(t); valores.push(base[0], base[1] + h, base[2]); };
  pon(0, 0);
  for (let i = 0; i <= 12; i++) pon(t0 + (subir * i) / 12, SUBIDA * suave(i / 12));
  const t1 = t0 + subir + arriba;
  for (let i = 0; i <= 12; i++) pon(t1 + (bajar * i) / 12, SUBIDA * (1 - suave(i / 12)));
  pon(CICLO, 0);
  const entradaT = doc.createAccessor().setType('SCALAR').setArray(new Float32Array(tiempos)).setBuffer(buffer);
  const salidaT = doc.createAccessor().setType('VEC3').setArray(new Float32Array(valores)).setBuffer(buffer);
  const sampler = doc.createAnimationSampler().setInput(entradaT).setOutput(salidaT).setInterpolation('LINEAR');
  const canal = doc.createAnimationChannel().setTargetNode(nodo).setTargetPath('translation').setSampler(sampler);
  anim.addSampler(sampler).addChannel(canal);
});

// «encuadre»: triángulo degenerado a la altura de las tapas subidas, para que el
// visor encuadre también la pieza abierta
const malla = raiz.listMeshes()[0];
const mat = malla.listPrimitives()[0].getMaterial();
let maxY = 0;
for (const n of raiz.listNodes()) {
  const m = n.getMesh();
  if (!m) continue;
  for (const p of m.listPrimitives()) maxY = Math.max(maxY, p.getAttribute('POSITION').getMax([])[1] + n.getTranslation()[1]);
}
const pos = doc.createAccessor().setType('VEC3').setBuffer(buffer)
  .setArray(new Float32Array([0, maxY + SUBIDA, 0, 0, maxY + SUBIDA, 0, 0, maxY + SUBIDA, 0]));
const prim = doc.createPrimitive().setAttribute('POSITION', pos).setMaterial(mat);
const encuadre = doc.createNode('encuadre').setMesh(doc.createMesh('encuadre').addPrimitive(prim));
raiz.listScenes()[0].addChild(encuadre);

await io.write(salida, doc);
console.log(salida, tapas.map((n) => n.getName()).join(', '));
