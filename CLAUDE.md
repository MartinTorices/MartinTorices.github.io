# Porfolio de Martín Torices: instrucciones para Claude

Web estática con Astro 7, publicada en https://martintorices.github.io. Cada push a `main` la despliega con GitHub Actions (`.github/workflows/deploy.yml`), en uno o dos minutos.

## Flujo de trabajo
1. Haz los cambios y ejecuta `npm install` si falta `node_modules`, luego `npm run build`. No publiques si falla.
2. Revisa visualmente con `npx astro preview` y capturas de Playwright: escritorio 1440 px y móvil 390 px, en modo claro y oscuro.
3. Haz commit en español, con un mensaje claro, y push a `main`.
4. Copia también los archivos cambiados a la carpeta local de Martín: `C:\Users\Usuario\Desktop\Trabajos\Trabajos internos\WEB`. Usa `device_commit_files`; la carpeta `.github` está protegida y no se copia.
5. Responde siempre en español de España y enséñale capturas del resultado.

## Dónde está cada cosa
- Datos personales, CV, programas y «Sobre mí» (ES/EN): `src/config.ts`
- Textos de la interfaz y rutas: `src/i18n.ts`
- Paleta y tipografía: `src/styles/global.css`
- Esquema de proyecto: `src/content.config.ts`
- Proyectos: `src/content/proyectos/<slug>/es.md`, `en.md` y sus imágenes
- Modelos 3D: `public/modelos/<slug>.glb`. Objetivo: menos de 10 MB. Si pesa más, simplifícalo (por ejemplo, con gltf-transform y compresión meshopt o draco).
- CV: `public/cv/`. Pon la ruta en `persona.cv`.

## Añadir un proyecto
- Pide a Martín: nombre, de qué trata, año, contexto (asignatura, concurso…), herramientas, fotos o renders, bocetos y el modelo (.glb, o expórtalo desde SolidWorks con Guardar como → Extended Reality).
- Redacta el caso de estudio en fases `##`: problema, bocetos, CAD, prototipo y resultado. Hazlo en ES y EN.
- Redacta con su voz (skill my-writing-style) y la norma RAE.
- Cuando haya proyectos reales, borra el proyecto de ejemplo: `src/content/proyectos/proyecto-ejemplo/` y `public/modelos/proyecto-ejemplo.glb`.

## Diseño
Concepto: hoja de plano técnico. Papel frío con retícula milimetrada, tinta azul-negra, azul de plano y rojo de revisión. En modo oscuro, cianotipia. Tipografía: Archivo Variable, jugando con su anchura. Mantén esta coherencia en los cambios.

## Cuidado
- El repositorio es público: nada confidencial y ningún CAD original.
- El teléfono no aparece escrito en el HTML: se monta con JavaScript en `Contacto.astro`.
