import { getCollection, type CollectionEntry } from 'astro:content';
import { rutas, t, type Lang } from './i18n';

export type Proyecto = CollectionEntry<'proyectos'> & { slug: string; lang: Lang };

// Devuelve los proyectos de un idioma, ordenados.
// Si un proyecto no tiene versión en inglés, se usa la española.
export async function proyectosDe(lang: Lang): Promise<Proyecto[]> {
  const todos = (await getCollection('proyectos', ({ data }) => !data.borrador)).map((p) => {
    const [slug, idioma] = p.id.split('/');
    return { ...p, slug, lang: idioma as Lang };
  });
  const slugs = [...new Set(todos.map((p) => p.slug))];
  return slugs
    .map((s) => todos.find((p) => p.slug === s && p.lang === lang) ?? todos.find((p) => p.slug === s && p.lang === 'es')!)
    .filter(Boolean)
    .sort((a, b) => a.data.orden - b.data.orden || b.data.anio - a.data.anio);
}

export type Grupo = Proyecto['data']['grupo'];

// Proyectos de un grupo: «principal» (mesa y galería) o «ingenieria-inversa»
export async function proyectosDeGrupo(lang: Lang, grupo: Grupo): Promise<Proyecto[]> {
  return (await proyectosDe(lang)).filter((p) => p.data.grupo === grupo);
}

// «Siguiente proyecto»: el que va detrás dentro de su mismo grupo (en bucle)
export function siguienteDe(lista: Proyecto[], proyecto: Proyecto): Proyecto | undefined {
  const grupo = lista.filter((p) => p.data.grupo === proyecto.data.grupo);
  const sig = grupo[(grupo.findIndex((p) => p.slug === proyecto.slug) + 1) % grupo.length];
  return sig && sig.slug !== proyecto.slug ? sig : undefined;
}

// Ficha de la mesa de la portada y de la galería: un proyecto grande o la carpeta
// «Ingeniería inversa», que agrupa todos los proyectos pequeños en una sola lámina.
export type Ficha = {
  clave: string;
  href: string;
  titulo: string;
  anio: string;
  portada: Proyecto['data']['portada'];
  portadaAlt: string;
  resumen: string;
  datos: string[];
  con3d: boolean;
  grupo: boolean; // true = lámina que agrupa varios proyectos (se ve como un taco)
};

export function fichaDe(p: Proyecto): Ficha {
  const { data } = p;
  return {
    clave: p.slug,
    href: rutas.proyecto(p.lang, p.slug),
    titulo: data.titulo,
    anio: String(data.anio),
    portada: data.portada,
    portadaAlt: data.portadaAlt,
    resumen: data.resumen,
    datos: [...(data.contexto ? [data.contexto] : []), ...data.herramientas],
    con3d: Boolean(data.modelo),
    grupo: false,
  };
}

// Lámina de «Ingeniería inversa»: portada del primer proyecto pequeño, años que abarca y número de piezas
export async function fichaInversa(lang: Lang): Promise<Ficha | undefined> {
  const piezas = await proyectosDeGrupo(lang, 'ingenieria-inversa');
  if (piezas.length === 0) return undefined;
  const tx = t(lang);
  const anios = piezas.map((p) => p.data.anio);
  const [min, max] = [Math.min(...anios), Math.max(...anios)];
  return {
    clave: 'ingenieria-inversa',
    href: rutas.inversa(lang),
    titulo: tx.inversaTitulo,
    anio: min === max ? String(min) : `${min}–${max}`,
    portada: piezas[0].data.portada,
    portadaAlt: piezas[0].data.portadaAlt,
    resumen: tx.inversaIntro,
    datos: [tx.inversaPiezas(piezas.length)],
    con3d: piezas.some((p) => p.data.modelo),
    grupo: true,
  };
}

// Mesa de la portada y galería de Proyectos: los proyectos grandes y, al final, la lámina de ingeniería inversa
export async function fichasPortada(lang: Lang): Promise<Ficha[]> {
  const grandes = (await proyectosDeGrupo(lang, 'principal')).map(fichaDe);
  const inversa = await fichaInversa(lang);
  return inversa ? [...grandes, inversa] : grandes;
}
