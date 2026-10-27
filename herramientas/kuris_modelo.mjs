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

  // ---------- anillo y cabeza (en el sistema del archivo de 3ds Max) ----------
  // El anillo, los tres brazos, los conos, las ruedas y el aro de luz forman un trípode
  // rígido que gira sobre su eje (para buscar apoyo) y se inclina en una rótula en el
  // centro del anillo hasta que las tres ruedas tocan el terreno. La cabeza (cúpula, ojo,
  // objetivo) va encima, siempre horizontal y mirando hacia donde avanza.
  const centroDe = (n) => { const b = getBounds(n); return b.min.map((v, i) => (v + b.max[i]) / 2); };
  const mallaDe = (n) => (n.getMesh() ?? n.listChildren()[0]?.getMesh())?.getName() ?? '';
  const bc0 = getBounds(cabeza);
  const C = [(bc0.min[0] + bc0.max[0]) / 2, (bc0.min[2] + bc0.max[2]) / 2];
  const tubo = getBounds(piezas.find((n) => mallaDe(n) === 'Tube001'));
  const rDisco = (tubo.max[0] - tubo.min[0]) / 2;
  const Praw = [C[0], (tubo.min[1] + tubo.max[1]) / 2, C[1]]; // rótula
  const DE_CABEZA = ['cabeza', 'luz ojos', 'ChamferCyl001', 'Object001'];
  const piezasCabeza = piezas.filter((n) => DE_CABEZA.includes(mallaDe(n)));
  const piezasAnillo = piezas.filter((n) => !DE_CABEZA.includes(mallaDe(n)));
  // ruedas: esferas (recortadas por arriba) de radio r; centro y arranque del brazo
  const Ro = (p) => [-p[2], p[1], p[0]]; // giro de −90° en Y (el dron mira hacia +z)
  const rel = (p) => Ro([p[0] - Praw[0], p[1] - Praw[1], p[2] - Praw[2]]);
  const ruedas = piezas.filter((n) => mallaDe(n) === 'Sphere001').map((rueda) => {
    const b = getBounds(rueda), cr = centroDe(rueda), r = (b.max[0] - b.min[0]) / 2;
    const a = Math.atan2(cr[2] - C[1], cr[0] - C[0]);
    const arranque = [C[0] + Math.cos(a) * rDisco, tubo.min[1], C[1] + Math.sin(a) * rDisco];
    return { r, w: rel([cr[0], b.min[1] + r, cr[2]]), s: rel(arranque) };
  });
  const fondoCabeza = bc0.min[1] - Praw[1];

  const kuris = doc.createNode('Kuris'); // en la rótula, con el rumbo de la marcha
  escena.addChild(kuris);
  const To = Ro(Praw).map((v) => -v);
  const orientCabeza = doc.createNode('cabeza_orientacion').setRotation(quatY(-Math.PI / 2)).setTranslation(To);
  const anillo = doc.createNode('anillo'); // giro e inclinación del trípode
  const orientAnillo = doc.createNode('anillo_orientacion').setRotation(quatY(-Math.PI / 2)).setTranslation(To);
  for (const p of piezasCabeza) { escena.removeChild(p); orientCabeza.addChild(p); }
  for (const p of piezasAnillo) { escena.removeChild(p); orientAnillo.addChild(p); }
  anillo.addChild(orientAnillo);
  kuris.addChild(orientCabeza).addChild(anillo);

  // ---------- relieves ----------
  // Bordillos bajo los carriles de las ruedas (de 0,65 a 1,9 del centro del camino), como
  // los bloques de los renders: la cabeza pasa siempre por encima, entre ellos, y como los
  // brazos están a 120° siempre hay una rueda en cada carril (a 1,43–1,65 del centro), así
  // que alguna sube a la fuerza, gire el anillo como gire.
  const carril = (zc, lado) => (lado > 0 ? [zc + 0.65, zc + 1.9] : [zc - 1.9, zc - 0.65]);
  const relieves = [
    { nombre: 'bordillo_delante', x0: -2.6, x1: 2.6, z: carril(ZDEL, 1), rampa: 0.5, alto: 0.4 },
    { nombre: 'bordillo_detras', x0: -2.6, x1: 2.6, z: carril(-ZDEL, -1), rampa: 0.5, alto: 0.32 },
  ].map((r) => ({ ...r, z0: r.z[0], z1: r.z[1] }));
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
  ];
  bloques.forEach(([x, z, l, h], i) => {
    escenario.addChild(doc.createNode(`bloque_${i}`).setMesh(
      caja(doc, buffer, `bloque_${i}`, [x - l / 2, 0, z - l / 2], [x + l / 2, h, z + l / 2], verde)));
  });

  // ---------- animación (cinemática del trípode) ----------
  const suelo = (x, z) => altura(x, z) + 0.006; // la cara de arriba de los relieves va 6 milésimas por encima
  const OFF = [];
  for (let i = -9; i <= 9; i++) for (let j = -9; j <= 9; j++) if (i * i + j * j <= 81) OFF.push([i / 9, j / 9]);
  const envolvente = (x, z, r) => {
    let m = r;
    for (const [dx, dz] of OFF) {
      const h = suelo(x + dx * r, z + dz * r);
      if (h > 0) m = Math.max(m, h + r * Math.sqrt(Math.max(0, 1 - dx * dx - dz * dz)));
    }
    return m;
  };
  const Ry = (p, a) => [p[0] * Math.cos(a) + p[2] * Math.sin(a), p[1], -p[0] * Math.sin(a) + p[2] * Math.cos(a)];
  const Rx = (p, a) => [p[0], p[1] * Math.cos(a) - p[2] * Math.sin(a), p[1] * Math.sin(a) + p[2] * Math.cos(a)];
  const Rz = (p, a) => [p[0] * Math.cos(a) - p[1] * Math.sin(a), p[0] * Math.sin(a) + p[1] * Math.cos(a), p[2]];
  // giro del anillo en el sistema del dron: primero gira φ sobre su eje, luego cabecea (x) y alabea (z)
  const Q = (p, phi, cab, ala) => Rx(Rz(Ry(p, phi), ala), cab);
  const qAnillo = (phi, cab, ala) => mulQ(mulQ(quatX(cab), [0, 0, Math.sin(ala / 2), Math.cos(ala / 2)]), quatY(phi));
  const mundo = (p, pose, u) => { const q = Ry(Q(p, pose.phi, u[1], u[2]), pose.yaw); return [q[0] + pose.x, q[1] + u[0], q[2] + pose.z]; };
  // y de la rótula, cabeceo y alabeo para que las tres ruedas apoyen (Gauss-Newton)
  const residuos = (pose, u) => ruedas.map((rd) => { const w = mundo(rd.w, pose, u); return w[1] - envolvente(w[0], w[2], rd.r); });
  const resolver3 = (A, b) => {
    const d = (m) => m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
    const D = d(A);
    return [0, 1, 2].map((c) => d(A.map((f, i) => f.map((v, j) => (j === c ? b[i] : v)))) / D);
  };
  const apoyar = (pose, u0) => {
    let u = u0 ? [...u0] : [0, 0, 0];
    if (!u0) { const r0 = residuos(pose, u); u[0] = -r0.reduce((a, b) => a + b, 0) / 3; }
    for (let it = 0; it < 25; it++) {
      const r = residuos(pose, u);
      if (Math.max(...r.map(Math.abs)) < 1e-6) break;
      const J = r.map(() => [0, 0, 0]);
      for (let k = 0; k < 3; k++) {
        const v = [...u]; v[k] += 1e-5;
        const rk = residuos(pose, v);
        for (let i = 0; i < 3; i++) J[i][k] = (rk[i] - r[i]) / 1e-5;
      }
      const du = resolver3(J, r.map((x) => -x));
      u = u.map((v, k) => v + Math.max(-0.2, Math.min(0.2, du[k])));
    }
    return u;
  };
  // holgura: brazos (del arranque a la rueda) y fondo de la cabeza sobre el terreno
  const choque = (pose, u, mb = 0.06, mc = 0.03) => {
    let peor = -Infinity;
    for (const rd of ruedas) {
      const a = mundo(rd.s, pose, u), b = mundo(rd.w, pose, u);
      for (let j = 1; j < 10; j++) {
        const q = j / 10;
        peor = Math.max(peor, suelo(a[0] + (b[0] - a[0]) * q, a[2] + (b[2] - a[2]) * q) + mb - (a[1] + (b[1] - a[1]) * q));
      }
    }
    for (const [dx, dz] of OFF) peor = Math.max(peor, suelo(pose.x + dx * 0.45, pose.z + dz * 0.45) + mc - (u[0] + fondoCabeza));
    return peor;
  };
  const inclinacion = (u) => Math.acos(Math.cos(u[1]) * Math.cos(u[2]));

  // empieza en la recta de la izquierda (llana), para cerrar el bucle con el anillo sin girar
  const F = 720;
  const S0 = 2 * RECTA_X + (RADIO * Math.PI) / 2 * 3 + 2 * RECTA_Z + 2 * RECTA_X + 2 * RECTA_Z / 2;
  const PHIS = []; for (let d = -60; d <= 60; d += 3) PHIS.push((d * Math.PI) / 180);
  const marcos = [];
  for (let i = 0; i <= F; i++) {
    const p = punto(S0 + (i / F) * L);
    const base = { x: p.x, z: p.z, yaw: Math.atan2(p.tx, p.tz) };
    const coste = PHIS.map((phi) => {
      const pose = { ...base, phi };
      const u = apoyar(pose);
      const res = Math.max(...residuos(pose, u).map(Math.abs));
      return (inclinacion(u) * 180) / Math.PI + 4 * Math.abs((phi * 180) / Math.PI) / 60 + 1e4 * Math.max(0, choque(pose, u)) + 1e4 * res;
    });
    marcos.push({ base, coste });
  }
  // camino de φ más barato (programación dinámica): poca inclinación, sin choques y sin giros bruscos
  const NP = PHIS.length, CERO = PHIS.findIndex((v) => Math.abs(v) < 1e-9), PASO = 2, KGIRO = 0.8;
  let acum = marcos[0].coste.map((c, j) => (j === CERO ? c : Infinity));
  const desde = [];
  for (let i = 1; i <= F; i++) {
    const nuevo = new Array(NP).fill(Infinity), arg = new Array(NP).fill(0);
    for (let j = 0; j < NP; j++) for (let d = -PASO; d <= PASO; d++) {
      const k = j + d; if (k < 0 || k >= NP) continue;
      const v = acum[k] + KGIRO * Math.abs(d) * 3 + marcos[i].coste[j];
      if (v < nuevo[j]) { nuevo[j] = v; arg[j] = k; }
    }
    desde.push(arg); acum = nuevo;
  }
  let j = CERO; const camino = [j];
  for (let i = F - 1; i >= 0; i--) { j = desde[i][j]; camino.unshift(j); }
  // suavizado del giro y solución exacta en cada fotograma
  let phis = camino.map((k) => PHIS[k]);
  for (let pasada = 0; pasada < 3; pasada++) phis = phis.map((v, i) => (i === 0 || i === F ? v : (phis[i - 1] + 2 * v + phis[i + 1]) / 4));

  const tiempos = [], tras = [], rots = [], somb = [], rotAn = [];
  const continuo = (lista, q) => {
    if (lista.length) {
      const k = lista.length - 4;
      if (q[0] * lista[k] + q[1] * lista[k + 1] + q[2] * lista[k + 2] + q[3] * lista[k + 3] < 0) q = q.map((v) => -v);
    }
    lista.push(...q);
  };
  let errMax = 0, incMax = 0, choqueMax = -Infinity, phiMax = 0, u = null;
  marcos.forEach(({ base }, i) => {
    const pose = { ...base, phi: phis[i] };
    u = apoyar(pose, u);
    errMax = Math.max(errMax, ...residuos(pose, u).map(Math.abs));
    incMax = Math.max(incMax, inclinacion(u));
    choqueMax = Math.max(choqueMax, choque(pose, u, 0, 0));
    phiMax = Math.max(phiMax, Math.abs(phis[i]));
    tiempos.push((i / F) * DURACION);
    tras.push(pose.x, u[0], pose.z);
    continuo(rots, quatY(pose.yaw));
    continuo(rotAn, qAnillo(pose.phi, u[1], u[2]));
    somb.push(0, altura(pose.x, pose.z) + 0.012 - u[0], 0);
  });
  const deg = (v) => ((v * 180) / Math.PI).toFixed(0);
  console.log(`  ruedas: error de apoyo máx. ${(errMax * 100).toFixed(2)} mm · inclinación del anillo hasta ${deg(incMax)}° · giro del anillo hasta ±${deg(phiMax)}° · solape real máx. ${(Math.max(0, choqueMax) * 100).toFixed(2)} mm (holgura mínima ${(-choqueMax * 100).toFixed(1)} mm)`);
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
  canal(anillo, 'rotation', rotAn, 'VEC4');
  // posición de partida (por si el visor no reproduce la animación)
  kuris.setTranslation(tras.slice(0, 3)).setRotation(rots.slice(0, 4));
  anillo.setRotation(rotAn.slice(0, 4));

  aEscalaReal(doc, escena);
  await io.write('public/modelos/kuris-marcha.glb', doc);
  console.log(`Guardado public/modelos/kuris-marcha.glb (circuito de ${L.toFixed(1)} u, ${DURACION} s)`);
}

await quieto();
await enMarcha();
