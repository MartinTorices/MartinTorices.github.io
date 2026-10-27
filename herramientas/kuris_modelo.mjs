// Modelos 3D del Kuris para la web.
//
// Uso: node herramientas/kuris_modelo.mjs <dronreal1.glb>
//
// Parte del .glb que Martín exportó de 3ds Max (versión blanca de la tienda) y crea:
//  - public/modelos/kuris.glb: el dron quieto, centrado y girado para que el ojo mire
//    casi a la cámara inicial del visor (32°).
//  - public/modelos/kuris-marcha.glb: el dron recorriendo en bucle (12 s) un circuito
//    sobre una plataforma verde con líneas de luz, como en los renders finales, con un
//    tramo con un badén para que se vea cómo salva el desnivel, y bloques alrededor.
// Los dos llevan:
//  - el anillo de luz blanca bajo el disco (no venía en el .glb);
//  - acabados con KHR_materials_variants: «bronce» (el de los renders finales, por
//    defecto), «blanco» (el de la tienda) y «arena» (el de las pruebas);
//  - materiales de luz con nombre «luz_…» (ojo y anillo): Visor3D.astro los apaga y
//    los enciende con el botón de la luz.
// Los colores base van en espacio lineal. Necesita @gltf-transform (devDependencies).

import { NodeIO, VertexLayout } from '@gltf-transform/core';
import {
  ALL_EXTENSIONS,
  KHRMaterialsEmissiveStrength,
  KHRMaterialsUnlit,
  KHRMaterialsVariants,
} from '@gltf-transform/extensions';
import { getBounds } from '@gltf-transform/functions';
import zlib from 'node:zlib';

const ENTRADA = process.argv[2];
if (!ENTRADA) {
  console.error('Uso: node herramientas/kuris_modelo.mjs <dronreal1.glb>');
  process.exit(1);
}
// Atributos separados (no intercalados): PiezaPlano.astro (three.js, mergeVertices)
// falla con los intercalados y el plano en alambre de la cabecera no sale.
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).setVertexLayout(VertexLayout.SEPARATE);
// El modelo de 3ds Max está a escala ×10: el Kuris real mide unos 318 × 121 × 362 mm.
const ESCALA = 0.1;
// mete todo lo que cuelga de la escena en un nodo a escala real (el glTF trabaja en metros)
function aEscalaReal(doc, escena) {
  const real = doc.createNode('escala_real').setScale([ESCALA, ESCALA, ESCALA]);
  for (const n of escena.listChildren()) {
    escena.removeChild(n);
    real.addChild(n);
  }
  escena.addChild(real);
}

// ---------- utilidades ----------
const lin = (v) => {
  v /= 255;
  return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
};
const color = (r, g, b, a = 1) => [lin(r), lin(g), lin(b), a];
const quatY = (a) => [0, Math.sin(a / 2), 0, Math.cos(a / 2)];
const quatX = (a) => [Math.sin(a / 2), 0, 0, Math.cos(a / 2)];
const mulQ = (a, b) => [
  a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
  a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
  a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
  a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2],
];

// PNG RGBA mínimo (para la sombra de contacto)
function png(w, h, pixel) {
  const crcT = new Uint32Array(256).map((_, n) => {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    return c >>> 0;
  });
  const crc = (buf) => {
    let c = 0xffffffff;
    for (const b of buf) c = crcT[(c ^ b) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  };
  const chunk = (tipo, datos) => {
    const t = Buffer.from(tipo);
    const len = Buffer.alloc(4);
    len.writeUInt32BE(datos.length);
    const c = Buffer.alloc(4);
    c.writeUInt32BE(crc(Buffer.concat([t, datos])));
    return Buffer.concat([len, t, datos, c]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) raw.set(pixel(x, y), y * (w * 4 + 1) + 1 + x * 4);
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw)),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

// ---------- materiales ----------
// nombre en 3ds Max -> [nuevo nombre, {variante: [color sRGB, metálico, rugosidad]}]
const ACABADOS = {
  plastico: ['carcasa', {
    bronce: [[66, 54, 40], 1, 0.24],
    blanco: [[232, 232, 228], 0, 0.28],
    arena: [[222, 190, 132], 0, 0.42],
  }],
  plastico_patas: ['brazos', {
    bronce: [[66, 54, 40], 1, 0.26],
    blanco: [[228, 224, 214], 0, 0.45],
    arena: [[214, 180, 122], 0, 0.45],
  }],
  Material__25: ['disco', {
    bronce: [[48, 40, 30], 1, 0.3],
    blanco: [[200, 198, 192], 0, 0.4],
    arena: [[190, 160, 110], 0, 0.45],
  }],
};
const VARIANTES = ['bronce', 'blanco', 'arena'];

function preparar(doc) {
  const root = doc.getRoot();
  const buffer = root.listBuffers()[0];
  const escena = root.getDefaultScene() ?? root.listScenes()[0];
  const fuerza = doc.createExtension(KHRMaterialsEmissiveStrength);
  const vx = doc.createExtension(KHRMaterialsVariants);
  const variantes = Object.fromEntries(VARIANTES.map((v) => [v, vx.createVariant(v)]));

  const crearMat = (nombre, [rgb, metal, rug]) =>
    doc.createMaterial(nombre)
      .setBaseColorFactor(color(...rgb))
      .setMetallicFactor(metal)
      .setRoughnessFactor(rug);

  // material de cada variante para las piezas de la carcasa
  const porVariante = new Map(); // material original -> {variante: material}
  for (const m of root.listMaterials()) {
    for (const e of m.listExtensions()) m.setExtension(e.extensionName, null);
    const def = ACABADOS[m.getName()];
    if (def) {
      const [nombre, vars] = def;
      const mats = {};
      for (const v of VARIANTES) mats[v] = crearMat(`${nombre}_${v}`, vars[v]);
      porVariante.set(m, mats);
    } else if (m.getName() === 'led_ojos') {
      m.setName('luz_ojo')
        .setBaseColorFactor(color(20, 60, 20))
        .setMetallicFactor(0)
        .setRoughnessFactor(0.3)
        .setEmissiveFactor([0.12, 1.0, 0.1])
        .setExtension(fuerza.extensionName, fuerza.createEmissiveStrength().setEmissiveStrength(2.5));
    } else if (m.getName() === 'plastico_bases_ruedas') {
      m.setName('bases_ruedas').setBaseColorFactor(color(22, 20, 17)).setMetallicFactor(0.3).setRoughnessFactor(0.45);
    } else if (m.getName() === 'goma_ruedas') {
      m.setName('ruedas').setBaseColorFactor(color(14, 14, 14)).setMetallicFactor(0).setRoughnessFactor(0.7);
    }
  }
  for (const malla of root.listMeshes()) {
    for (const p of malla.listPrimitives()) {
      const mats = porVariante.get(p.getMaterial());
      if (!mats) continue;
      p.setMaterial(mats.bronce);
      const lista = vx.createMappingList();
      for (const v of VARIANTES) lista.addMapping(vx.createMapping().setMaterial(mats[v]).addVariant(variantes[v]));
      p.setExtension(vx.extensionName, lista);
    }
  }
  for (const m of porVariante.keys()) m.dispose();

  // ---------- anillo de luz bajo el disco ----------
  const tubo = root.listNodes().find((n) => n.getName() === 'Tube001');
  const bt = getBounds(tubo);
  const cx = (bt.min[0] + bt.max[0]) / 2;
  const cz = (bt.min[2] + bt.max[2]) / 2;
  const R = ((bt.max[0] - bt.min[0]) / 2) * 0.9;
  const anillo = doc.createNode('anillo_luz')
    .setMesh(toro(doc, buffer, 'anillo_luz', R, R * 0.03,
      doc.createMaterial('luz_anillo')
        .setBaseColorFactor(color(110, 110, 106))
        .setRoughnessFactor(0.3)
        .setMetallicFactor(0)
        .setEmissiveFactor([1, 1, 1])
        .setExtension(fuerza.extensionName, fuerza.createEmissiveStrength().setEmissiveStrength(2.5))))
    .setTranslation([cx, bt.min[1] - R * 0.03, cz]);
  escena.addChild(anillo);

  const piezas = escena.listChildren();
  const cabeza = root.listNodes().find((n) => n.getName() === 'cabeza');
  return { root, buffer, escena, piezas, cabeza };
}

// ---------- geometría ----------
function mallaDesde(doc, buffer, nombre, pos, nor, idx, mat, uv) {
  const prim = doc.createPrimitive()
    .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array(pos)).setBuffer(buffer))
    .setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(new Float32Array(nor)).setBuffer(buffer))
    .setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint32Array(idx)).setBuffer(buffer))
    .setMaterial(mat);
  if (uv) prim.setAttribute('TEXCOORD_0', doc.createAccessor().setType('VEC2').setArray(new Float32Array(uv)).setBuffer(buffer));
  return doc.createMesh(nombre).addPrimitive(prim);
}

function toro(doc, buffer, nombre, R, r, mat, nu = 96, nv = 12) {
  const pos = [], nor = [], idx = [];
  for (let i = 0; i <= nu; i++) {
    const u = (i / nu) * Math.PI * 2;
    for (let j = 0; j <= nv; j++) {
      const v = (j / nv) * Math.PI * 2;
      const nx = Math.cos(v) * Math.cos(u), ny = Math.sin(v), nz = Math.cos(v) * Math.sin(u);
      pos.push((R + r * Math.cos(v)) * Math.cos(u), r * Math.sin(v), (R + r * Math.cos(v)) * Math.sin(u));
      nor.push(nx, ny, nz);
    }
  }
  for (let i = 0; i < nu; i++)
    for (let j = 0; j < nv; j++) {
      const a = i * (nv + 1) + j, b = a + nv + 1;
      idx.push(a, a + 1, b, b, a + 1, b + 1);
    }
  return mallaDesde(doc, buffer, nombre, pos, nor, idx, mat);
}

// caja (con caras planas) entre min y max
function caja(doc, buffer, nombre, min, max, mat) {
  const [x0, y0, z0] = min, [x1, y1, z1] = max;
  const caras = [
    [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1], [1, 0, 0]],
    [[x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [x0, y0, z0], [-1, 0, 0]],
    [[x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [0, 1, 0]],
    [[x0, y0, z1], [x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [0, -1, 0]],
    [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], [0, 0, 1]],
    [[x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0], [0, 0, -1]],
  ];
  const pos = [], nor = [], idx = [];
  caras.forEach(([a, b, c, d, n], k) => {
    pos.push(...a, ...b, ...c, ...d);
    for (let i = 0; i < 4; i++) nor.push(...n);
    idx.push(4 * k, 4 * k + 1, 4 * k + 2, 4 * k, 4 * k + 2, 4 * k + 3);
  });
  return mallaDesde(doc, buffer, nombre, pos, nor, idx, mat);
}

// ---------- dron quieto ----------
async function quieto() {
  const doc = await io.read(ENTRADA);
  const { escena, piezas } = preparar(doc);
  const kuris = doc.createNode('Kuris').setRotation(quatY((-80 * Math.PI) / 180));
  for (const p of piezas) {
    escena.removeChild(p);
    kuris.addChild(p);
  }
  escena.addChild(kuris);
  const b = getBounds(kuris);
  kuris.setTranslation([-(b.min[0] + b.max[0]) / 2, -b.min[1], -(b.min[2] + b.max[2]) / 2]);
  aEscalaReal(doc, escena);
  await io.write('public/modelos/kuris.glb', doc);
  console.log('Guardado public/modelos/kuris.glb');
}

// ---------- dron en marcha ----------
// Circuito: rectángulo de esquinas redondeadas (línea central) sobre una plataforma.
// En la recta de delante hay un bloque con rampas que ocupa todo el camino; en la de
// detrás, un escalón estrecho que solo pisa una rueda. Cada brazo gira en su arranque
// (bisagra en el borde del disco) para que su rueda siga el terreno, como en los renders
// finales apoyados en bloques de distinta altura; el cuerpo va nivelado, a la altura media
// de las tres ruedas, así que cuando una rueda sube, las otras dos bajan un poco.
const RECTA_X = 1.6, RECTA_Z = 0.6, RADIO = 1.9, ANCHO = 3.0;
const PLAT = { x: 5.9, z: 4.9, grosor: 0.3 };
const DURACION = 12;
const ZDEL = RECTA_Z + RADIO; // línea central de la recta de delante (z > 0) y de detrás (-ZDEL)

// punto del circuito a una distancia s (0..L) y su tangente
function circuito() {
  const tramos = [];
  const recta = (x0, z0, x1, z1) => tramos.push({ tipo: 'r', x0, z0, x1, z1, L: Math.hypot(x1 - x0, z1 - z0) });
  const curva = (cx, cz, a0) => tramos.push({ tipo: 'c', cx, cz, a0, L: (RADIO * Math.PI) / 2 });
  recta(-RECTA_X, ZDEL, RECTA_X, ZDEL);
  curva(RECTA_X, RECTA_Z, Math.PI / 2);
  recta(RECTA_X + RADIO, RECTA_Z, RECTA_X + RADIO, -RECTA_Z);
  curva(RECTA_X, -RECTA_Z, 0);
  recta(RECTA_X, -ZDEL, -RECTA_X, -ZDEL);
  curva(-RECTA_X, -RECTA_Z, -Math.PI / 2);
  recta(-RECTA_X - RADIO, -RECTA_Z, -RECTA_X - RADIO, RECTA_Z);
  curva(-RECTA_X, RECTA_Z, -Math.PI);
  const L = tramos.reduce((a, t) => a + t.L, 0);
  const punto = (s) => {
    s = ((s % L) + L) % L;
    for (const t of tramos) {
      if (s <= t.L) {
        if (t.tipo === 'r') {
          const k = s / t.L, tx = (t.x1 - t.x0) / t.L, tz = (t.z1 - t.z0) / t.L;
          return { x: t.x0 + (t.x1 - t.x0) * k, z: t.z0 + (t.z1 - t.z0) * k, tx, tz };
        }
        const a = t.a0 - s / RADIO;
        return { x: t.cx + RADIO * Math.cos(a), z: t.cz + RADIO * Math.sin(a), tx: Math.sin(a), tz: -Math.cos(a) };
      }
      s -= t.L;
    }
  };
  return { L, punto };
}

// Relieves: bloques con rampas a lo largo de x (en la dirección de la marcha)
// { x0, x1, z0, z1, rampa, alto }: de x0 a x0 + rampa sube, de x1 - rampa a x1 baja.
const suave = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
function alturaRelieve(r, x, z) {
  if (x <= r.x0 || x >= r.x1 || z < r.z0 || z > r.z1) return 0;
  return r.alto * Math.min(suave((x - r.x0) / r.rampa), suave((r.x1 - x) / r.rampa));
}

function relieveMalla(doc, buffer, nombre, r, mat) {
  const pos = [], nor = [], idx = [];
  const M = 60;
  const xs = Array.from({ length: M + 1 }, (_, i) => r.x0 + ((r.x1 - r.x0) * i) / M);
  const h = (x) => alturaRelieve({ ...r, z0: -1e9, z1: 1e9 }, x, 0) + 0.006;
  // cara de arriba (normales según la pendiente)
  for (const x of xs) {
    const d = (h(x + 0.01) - h(x - 0.01)) / 0.02, n = Math.hypot(d, 1);
    for (const z of [r.z0, r.z1]) { pos.push(x, h(x), z); nor.push(-d / n, 1 / n, 0); }
  }
  for (let i = 0; i < M; i++) { const a = 2 * i; idx.push(a, a + 1, a + 2, a + 2, a + 1, a + 3); }
  // caras laterales
  for (const [z, nz] of [[r.z1, 1], [r.z0, -1]]) {
    const base = pos.length / 3;
    for (const x of xs) { pos.push(x, 0, z, x, h(x), z); nor.push(0, 0, nz, 0, 0, nz); }
    for (let i = 0; i < M; i++) {
      const a = base + 2 * i;
      if (nz > 0) idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
      else idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
  }
  return mallaDesde(doc, buffer, nombre, pos, nor, idx, mat);
}

// cuaternión de un giro de «ang» alrededor del eje unitario «e»
const quatEje = (e, ang) => [e[0] * Math.sin(ang / 2), e[1] * Math.sin(ang / 2), e[2] * Math.sin(ang / 2), Math.cos(ang / 2)];

async function enMarcha() {
  const doc = await io.read(ENTRADA);
  const { buffer, escena, piezas, cabeza } = preparar(doc);
  const unlit = doc.createExtension(KHRMaterialsUnlit);
  const fuerza = doc.createExtension(KHRMaterialsEmissiveStrength);

  // ---------- brazos articulados (en el sistema del archivo de 3ds Max) ----------
  const centroDe = (n) => { const b = getBounds(n); return b.min.map((v, i) => (v + b.max[i]) / 2); };
  const mallaDe = (n) => (n.getMesh() ?? n.listChildren()[0]?.getMesh())?.getName() ?? '';
  const bc0 = getBounds(cabeza);
  const C = [(bc0.min[0] + bc0.max[0]) / 2, (bc0.min[2] + bc0.max[2]) / 2];
  const suelo0 = getBounds(escena.listChildren().find((n) => mallaDe(n) === 'Sphere001')).min[1];
  const tubo = getBounds(escena.listChildren().find((n) => mallaDe(n) === 'Tube001'));
  const rDisco = (tubo.max[0] - tubo.min[0]) / 2;
  const angulo = (p) => Math.atan2(p[2] - C[1], p[0] - C[0]);
  const ruedas = piezas.filter((n) => mallaDe(n) === 'Sphere001');
  const patas = ruedas.map((rueda, k) => {
    const cr = centroDe(rueda), ar = angulo(cr);
    const cerca = (nombre) => piezas.filter((n) => mallaDe(n) === nombre)
      .sort((a, b) => Math.abs(Math.sin((angulo(centroDe(a)) - ar) / 2)) - Math.abs(Math.sin((angulo(centroDe(b)) - ar) / 2)))[0];
    const partes = [rueda, cerca('Cone001'), cerca('Loft001')];
    const u = [Math.cos(ar), 0, Math.sin(ar)]; // hacia fuera, en horizontal
    const bisagra = [C[0] + u[0] * rDisco * 0.9, suelo0 + (tubo.min[1] - suelo0) * 0.95, C[1] + u[2] * rDisco * 0.9];
    const eje = [-u[2], 0, u[0]]; // Y × u: con ángulo positivo la rueda baja
    const Lh = Math.hypot(cr[0] - bisagra[0], cr[2] - bisagra[2]);
    const vy = suelo0 - bisagra[1];
    const nodo = doc.createNode(`brazo_${k}`).setTranslation(bisagra);
    const offs = doc.createNode(`brazo_${k}_piezas`).setTranslation(bisagra.map((v) => -v));
    nodo.addChild(offs);
    for (const p of partes) { escena.removeChild(p); offs.addChild(p); }
    escena.addChild(nodo);
    // ángulo para que la rueda suba dh (bisección; y(θ) = vy·cosθ − Lh·senθ)
    const anguloPara = (dh) => {
      let a = -1.2, b = 1.2;
      for (let i = 0; i < 50; i++) {
        const m = (a + b) / 2;
        if (vy * Math.cos(m) - Lh * Math.sin(m) - vy > dh) a = m; else b = m;
      }
      return (a + b) / 2;
    };
    return { nodo, rueda, eje, anguloPara };
  });

  // el dron mira hacia +z local, centrado en la cabeza y con las ruedas en y = 0
  const orient = doc.createNode('orientacion').setRotation(quatY(-Math.PI / 2));
  for (const p of escena.listChildren()) { escena.removeChild(p); orient.addChild(p); }
  const kuris = doc.createNode('Kuris').addChild(orient);
  escena.addChild(kuris);
  const bc = getBounds(cabeza), bt = getBounds(orient);
  orient.setTranslation([-(bc.min[0] + bc.max[0]) / 2, -bt.min[1], -(bc.min[2] + bc.max[2]) / 2]);
  // posición de cada rueda en el sistema del dron (x, z)
  for (const p of patas) { const c = centroDe(p.rueda); p.w = [c[0], c[2]]; }

  // ---------- relieves ----------
  // escalón de detrás: centrado en la huella de la rueda que va por el lado interior
  // (el dron va hacia −x, yaw −90°: la rueda en w pasa por z = −ZDEL + w.x)
  const interior = patas.reduce((a, p) => (p.w[0] > a.w[0] ? p : a));
  const zEsc = -ZDEL + interior.w[0];
  const relieves = [
    { nombre: 'rampa', x0: -1.55, x1: 1.55, z0: ZDEL - ANCHO / 2 - 0.06, z1: ZDEL + ANCHO / 2 + 0.06, rampa: 0.6, alto: 0.7 },
    { nombre: 'escalon', x0: -1.0, x1: 1.0, z0: zEsc - 0.45, z1: zEsc + 0.45, rampa: 0.35, alto: 0.6 },
  ];
  const altura = (x, z) => Math.max(0, ...relieves.map((r) => alturaRelieve(r, x, z)));

  // sombra de contacto (la de model-viewer solo cae en el suelo, no en la plataforma)
  const T = 128;
  const sombraTex = doc.createTexture('sombra').setMimeType('image/png').setImage(png(T, T, (x, y) => {
    const r = Math.hypot((x + 0.5) / T - 0.5, (y + 0.5) / T - 0.5) * 2;
    const k = Math.min(1, Math.max(0, (r - 0.25) / 0.75));
    return [0, 0, 0, Math.round(150 * (1 - k * k * (3 - 2 * k)))];
  }));
  const matSombra = doc.createMaterial('sombra').setBaseColorFactor([1, 1, 1, 1]).setBaseColorTexture(sombraTex)
    .setAlphaMode('BLEND').setExtension(unlit.extensionName, unlit.createUnlit());
  const S = 1.9;
  const sombra = doc.createNode('sombra_contacto').setTranslation([0, 0.012, 0]).setMesh(
    mallaDesde(doc, buffer, 'sombra_contacto',
      [-S, 0, -S, S, 0, -S, S, 0, S, -S, 0, S], [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
      [0, 2, 1, 0, 3, 2], matSombra, [0, 0, 1, 0, 1, 1, 0, 1]));
  kuris.addChild(sombra);

  // ---------- escenario ----------
  const escenario = doc.createNode('escenario');
  escena.addChild(escenario);
  const verdeOscuro = doc.createMaterial('plataforma').setBaseColorFactor(color(14, 52, 18)).setRoughnessFactor(0.55);
  const verde = doc.createMaterial('bloques').setBaseColorFactor(color(24, 96, 30)).setRoughnessFactor(0.4);
  const asfalto = doc.createMaterial('camino').setBaseColorFactor(color(34, 38, 33)).setRoughnessFactor(0.85);
  const neon = doc.createMaterial('neon').setBaseColorFactor(color(240, 240, 235)).setEmissiveFactor([1, 1, 1])
    .setExtension(fuerza.extensionName, fuerza.createEmissiveStrength().setEmissiveStrength(1.6));

  escenario.addChild(doc.createNode('plataforma').setMesh(
    caja(doc, buffer, 'plataforma', [-PLAT.x, -PLAT.grosor, -PLAT.z], [PLAT.x, 0, PLAT.z], verdeOscuro)));
  const g = 0.05;
  for (const [n, min, max] of [
    ['borde_delante', [-PLAT.x, 0, PLAT.z - g], [PLAT.x, 0.006, PLAT.z]],
    ['borde_detras', [-PLAT.x, 0, -PLAT.z], [PLAT.x, 0.006, -PLAT.z + g]],
    ['borde_der', [PLAT.x - g, 0, -PLAT.z], [PLAT.x, 0.006, PLAT.z]],
    ['borde_izq', [-PLAT.x, 0, -PLAT.z], [-PLAT.x + g, 0.006, PLAT.z]],
  ]) escenario.addChild(doc.createNode(n).setMesh(caja(doc, buffer, n, min, max, neon)));

  // camino plano con líneas de luz en los bordes (los relieves van encima)
  const { L, punto } = circuito();
  const N = 480;
  const filas = (desde, hasta, alto) => {
    const pos = [], nor = [], idx = [];
    for (let i = 0; i <= N; i++) {
      const p = punto((i / N) * L);
      const nx = -p.tz, nz = p.tx;
      for (const o of [desde, hasta]) { pos.push(p.x + nx * o, alto, p.z + nz * o); nor.push(0, 1, 0); }
    }
    for (let i = 0; i < N; i++) { const a = 2 * i; idx.push(a, a + 1, a + 2, a + 2, a + 1, a + 3); }
    return { pos, nor, idx };
  };
  const c = filas(-ANCHO / 2, ANCHO / 2, 0.004);
  escenario.addChild(doc.createNode('camino').setMesh(mallaDesde(doc, buffer, 'camino', c.pos, c.nor, c.idx, asfalto)));
  for (const [n, o] of [['linea_izq', ANCHO / 2], ['linea_der', -ANCHO / 2]]) {
    const l = filas(o - 0.035, o + 0.035, 0.008);
    escenario.addChild(doc.createNode(n).setMesh(mallaDesde(doc, buffer, n, l.pos, l.nor, l.idx, neon)));
  }
  for (const r of relieves) escenario.addChild(doc.createNode(r.nombre).setMesh(relieveMalla(doc, buffer, r.nombre, r, verde)));
  // bloques verdes de adorno, fuera del camino
  const bloques = [
    [-5.0, 4.0, 0.9, 0.7], [5.1, 4.0, 0.7, 1.1], [5.0, -4.0, 1.0, 0.6], [-5.0, -4.0, 0.8, 1.3],
    [-0.5, 0, 0.9, 0.5], [0.9, -0.1, 0.6, 0.9],
  ];
  bloques.forEach(([x, z, l, h], i) => {
    escenario.addChild(doc.createNode(`bloque_${i}`).setMesh(
      caja(doc, buffer, `bloque_${i}`, [x - l / 2, 0, z - l / 2], [x + l / 2, h, z + l / 2], verde)));
  });

  // ---------- animación ----------
  const F = 720;
  const tiempos = [], tras = [], rots = [], somb = [];
  const angs = patas.map(() => []);
  const continuo = (lista, q) => {
    if (lista.length) {
      const k = lista.length - 4;
      if (q[0] * lista[k] + q[1] * lista[k + 1] + q[2] * lista[k + 2] + q[3] * lista[k + 3] < 0) q = q.map((v) => -v);
    }
    lista.push(...q);
  };
  for (let i = 0; i <= F; i++) {
    const s = (i / F) * L;
    const p = punto(s);
    const yaw = Math.atan2(p.tx, p.tz);
    const cs = Math.cos(yaw), sn = Math.sin(yaw);
    // altura del terreno bajo cada rueda
    const h = patas.map(({ w }) => altura(p.x + w[0] * cs + w[1] * sn, p.z - w[0] * sn + w[1] * cs));
    const yCuerpo = h.reduce((a, b) => a + b, 0) / h.length;
    tiempos.push((i / F) * DURACION);
    tras.push(p.x, yCuerpo, p.z);
    continuo(rots, quatY(yaw));
    somb.push(0, altura(p.x, p.z) + 0.012 - yCuerpo, 0);
    patas.forEach((pt, k) => continuo(angs[k], quatEje(pt.eje, pt.anguloPara(h[k] - yCuerpo))));
  }
  const entrada = doc.createAccessor().setType('SCALAR').setArray(new Float32Array(tiempos)).setBuffer(buffer);
  const anim = doc.createAnimation('en_marcha');
  const canal = (nodo, ruta, datos, tipo) => {
    const sampler = doc.createAnimationSampler().setInput(entrada).setInterpolation('LINEAR')
      .setOutput(doc.createAccessor().setType(tipo).setArray(new Float32Array(datos)).setBuffer(buffer));
    anim.addSampler(sampler).addChannel(doc.createAnimationChannel().setTargetNode(nodo).setTargetPath(ruta).setSampler(sampler));
  };
  canal(kuris, 'translation', tras, 'VEC3');
  canal(kuris, 'rotation', rots, 'VEC4');
  canal(sombra, 'translation', somb, 'VEC3');
  patas.forEach((pt, k) => canal(pt.nodo, 'rotation', angs[k], 'VEC4'));
  // posición de partida (por si el visor no reproduce la animación)
  kuris.setTranslation(tras.slice(0, 3)).setRotation(rots.slice(0, 4));

  aEscalaReal(doc, escena);
  await io.write('public/modelos/kuris-marcha.glb', doc);
  const maxAng = Math.max(...angs.flatMap((a) => a.filter((_, j) => j % 4 === 3).map((w) => (2 * Math.acos(Math.min(1, Math.abs(w))) * 180) / Math.PI)));
  console.log(`Guardado public/modelos/kuris-marcha.glb (circuito de ${L.toFixed(1)} u, ${DURACION} s, brazos hasta ±${maxAng.toFixed(0)}°)`);
  console.log('ruedas (x, z en el dron):', patas.map((p) => p.w.map((v) => v.toFixed(2)).join(', ')).join(' | '), '· escalón en z =', zEsc.toFixed(2));
}

await quieto();
await enMarcha();
