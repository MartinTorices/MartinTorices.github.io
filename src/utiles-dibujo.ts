// Útiles de dibujo para la mesa de la portada, dibujados en SVG como en un plano:
// escuadra y cartabón de metacrilato (transparentes, con graduación), escalímetro
// y portaminas. Las medidas del viewBox van en milímetros reales.
// Los colores salen de las variables de la web (--tinta-suave, --azul…).

const TRAZO = 'stroke="var(--util-trazo)" stroke-linejoin="round" vector-effect="non-scaling-stroke"';

// Triángulo rectángulo con el hueco interior paralelo (a «d» mm del borde)
function triangulo(ancho: number, alto: number, d: number) {
  const c = Math.hypot(ancho, alto);
  const r = (ancho + alto - c) / 2; // radio inscrito
  const ix = r;
  const iy = alto - r; // incentro (ángulo recto abajo a la izquierda)
  const k = (r - d) / r;
  const p = [
    [0, alto],
    [ancho, alto],
    [0, 0],
  ];
  const q = p.map(([x, y]) => [ix + (x - ix) * k, iy + (y - iy) * k]);
  const ruta = (pts: number[][]) => `M${pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join('L')}Z`;
  return { exterior: ruta(p), interior: ruta(q) };
}

// Graduación a lo largo del borde inferior (cada 1 mm, más larga cada 5 y cada 10)
function regla(largo: number, y: number, hacia: 1 | -1, desde = 4, numeros = true, cada = 10) {
  let lineas = '';
  let textos = '';
  for (let mm = 0; mm <= largo - desde - 22; mm += 1) {
    const x = desde + mm;
    const l = mm % 10 === 0 ? 7 : mm % 5 === 0 ? 4.5 : 2.5;
    lineas += `M${x} ${y}v${hacia * l}`;
    if (numeros && mm % cada === 0 && mm > 0) {
      textos += `<text x="${x}" y="${y + hacia * 12}" text-anchor="middle">${mm / 10}</text>`;
    }
  }
  return `<path d="${lineas}" stroke="var(--util-trazo)" stroke-width="0.5" vector-effect="non-scaling-stroke"/>` + textos;
}

function plantilla(ancho: number, alto: number, d: number, conRegla: number) {
  const t = triangulo(ancho, alto, d);
  return `<svg viewBox="-2 -2 ${ancho + 4} ${alto + 4}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path class="util__forma" d="${t.exterior} ${t.interior}" fill-rule="evenodd" fill="var(--util-acrilico)" ${TRAZO} stroke-width="1.2"/>
    <path d="${t.interior}" fill="none" ${TRAZO} stroke-width="0.8" opacity="0.6"/>
    <g class="util__regla" font-size="6" fill="var(--util-trazo)">${regla(conRegla, alto, -1)}</g>
  </svg>`;
}

export const escuadra = plantilla(250, 250, 34, 250);
export const cartabon = plantilla(300, 173, 26, 300);

// Escalímetro triangular visto desde arriba: dos caras con escalas distintas
export const escalimetro = (() => {
  const L = 300;
  const H = 28;
  const caras = (escala: string, y: number, hacia: 1 | -1) => {
    let lineas = '';
    let textos = '';
    for (let mm = 0; mm <= 280; mm += 2) {
      const x = 10 + mm;
      const l = mm % 20 === 0 ? 6 : mm % 10 === 0 ? 4 : 2.2;
      lineas += `M${x} ${y}v${hacia * l}`;
      if (mm % 40 === 0) textos += `<text x="${x}" y="${y + hacia * 10.5}" text-anchor="middle">${mm / 10}</text>`;
    }
    return `<path d="${lineas}" stroke="var(--lamina-tinta)" stroke-width="0.45" vector-effect="non-scaling-stroke"/>${textos}<text x="${L - 6}" y="${y + hacia * 10.5}" text-anchor="end" font-weight="700">${escala}</text>`;
  };
  return `<svg viewBox="-1 -1 ${L + 2} ${H + 2}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <rect class="util__forma" width="${L}" height="${H}" rx="1.5" fill="var(--lamina-fondo)" stroke="var(--lamina-fondo-2)" stroke-width="1" vector-effect="non-scaling-stroke"/>
    <path d="M0 ${H / 2}H${L}" stroke="var(--lamina-fondo-2)" stroke-width="1.4" vector-effect="non-scaling-stroke"/>
    <g font-size="4.6" fill="var(--lamina-tinta)">${caras('1:100', 0.5, 1)}${caras('1:50', H - 0.5, -1)}</g>
  </svg>`;
})();

// Portaminas: cuerpo, grip estriado, punta metálica, mina, clip y pulsador amarillo
export const portaminas = (() => {
  let estrias = '';
  for (let x = 40; x <= 78; x += 3) estrias += `M${x} 8.2v7.6`;
  return `<svg viewBox="-1 -1 152 26" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path class="util__forma" d="M0 12 L10 10.6 L22 9 V15 L10 13.4 Z" fill="var(--util-metal)" ${TRAZO} stroke-width="0.9"/>
    <path d="M-1 12h2" stroke="var(--util-trazo)" stroke-width="1" vector-effect="non-scaling-stroke"/>
    <rect class="util__forma" x="22" y="7" width="120" height="10" rx="2" fill="var(--util-cuerpo)" ${TRAZO} stroke-width="1"/>
    <path d="${estrias}" stroke="var(--util-trazo)" stroke-width="0.5" opacity="0.7" vector-effect="non-scaling-stroke"/>
    <rect class="util__forma" x="142" y="8.5" width="8" height="7" rx="1.2" fill="var(--azul)"/>
    <path class="util__forma" d="M108 7 V2.5 Q108 1 110 1 H136 Q138 1 138 2.5 V4" fill="none" ${TRAZO} stroke-width="1"/>
  </svg>`;
})();
