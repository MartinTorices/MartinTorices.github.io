// Mapa del sitio para Google (https://martintorices.github.io/sitemap.xml).
// Cada página va con su versión en el otro idioma (hreflang), para que Google
// enseñe la española o la inglesa según quien busque.
import type { APIRoute } from 'astro';
import { proyectosDe, proyectosDeGrupo } from '../proyectos';
import { rutas } from '../i18n';

export const GET: APIRoute = async ({ site }) => {
  const url = (ruta: string) => new URL(ruta, site).href;
  const pares: [string, string][] = [
    [rutas.inicio('es'), rutas.inicio('en')],
    [rutas.proyectos('es'), rutas.proyectos('en')],
    ...((await proyectosDeGrupo('es', 'ingenieria-inversa')).length ? [[rutas.inversa('es'), rutas.inversa('en')] as [string, string]] : []),
    ...(await proyectosDe('es')).map((p): [string, string] => [rutas.proyecto('es', p.slug), rutas.proyecto('en', p.slug)]),
  ];
  const entrada = (ruta: string, es: string, en: string) => `  <url>
    <loc>${url(ruta)}</loc>
    <xhtml:link rel="alternate" hreflang="es" href="${url(es)}"/>
    <xhtml:link rel="alternate" hreflang="en" href="${url(en)}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="${url(es)}"/>
  </url>`;
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${pares.flatMap(([es, en]) => [entrada(es, es, en), entrada(en, es, en)]).join('\n')}
</urlset>
`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
