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
