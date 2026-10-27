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
      equipo: z.array(z.string()).default([]), // compañeros, si fue en grupo
      rol: z.string().optional(), // tu papel en el equipo
      etiquetas: z.array(z.string()).default([]),
      portada: image(),
      portadaAlt: z.string(),
      modelo: z.string().optional(), // p. ej. '/modelos/mi-proyecto.glb'
      modeloAlt: z.string().optional(), // descripción del modelo 3D (si no, se usa portadaAlt)
      // Versiones del modelo a elegir en el visor (la primera o la que coincida con «modelo» sale al principio)
      // «orbita» (opcional): ángulo de cámara al elegir esa versión, p. ej. '30deg 60deg 80%'
      modeloVariantes: z.array(z.object({ nombre: z.string(), src: z.string(), orbita: z.string().optional() })).default([]),
      etiquetaVariantes: z.string().optional(), // p. ej. 'Balda'
      // Acabados del modelo (KHR_materials_variants dentro del .glb): nombre visible y nombre de la variante
      acabados: z.array(z.object({ nombre: z.string(), variante: z.string() })).default([]),
      etiquetaAcabados: z.string().optional(), // p. ej. 'Acabado'
      // Botón para encender y apagar las luces del modelo (materiales cuyo nombre empieza por «luz_»)
      interruptorLuz: z.boolean().default(false),
      orden: z.number().default(100), // menor = aparece antes
      borrador: z.boolean().default(false), // true = no se publica
    }),
});

export const collections = { proyectos };
