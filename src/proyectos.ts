import { getCollection, type CollectionEntry } from 'astro:content';
import type { Lang } from './i18n';

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
