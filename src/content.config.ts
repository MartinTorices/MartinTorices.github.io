import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// ============================================================
//  PROYECTOS
//  Cada proyecto es una carpeta dentro de src/content/proyectos/
//  con dos archivos: es.md (español) y en.md (inglés),
//  más sus imágenes. El modelo 3D (.glb) va en public/modelos/.
// ============================================================
const proyectos = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/proyectos' }),
  schema: ({ image }) =>
    z.object({
      titulo: z.string(),
      resumen: z.string(),
      anio: z.number(),
      contexto: z.string().optional(), // asignatura, concurso, encargo...
      herramientas: z.array(z.string()).default([]),
      etiquetas: z.array(z.string()).default([]),
      portada: image(),
      portadaAlt: z.string(),
      modelo: z.string().optional(), // p. ej. '/modelos/mi-proyecto.glb'
      orden: z.number().default(100), // menor = aparece antes
      borrador: z.boolean().default(false), // true = no se publica
    }),
});

export const collections = { proyectos };
