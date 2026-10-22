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
- Si fue en grupo, rellena `equipo` (nombres completos de los compañeros) y `rol` (su papel).
- Imágenes en el Markdown: varias líneas `![alt](./img.jpg)` seguidas en el mismo párrafo se ponen en fila; una línea `*texto*` justo debajo (sin línea en blanco) es el pie de foto. Los planos `.svg` exportados de CATIA o SolidWorks se apilan y se invierten solos en modo oscuro (limpia antes el SVG: atributos sin espacios alrededor de `=`, viewBox recortado y width/height en números).
- Las tablas de Markdown salen con aspecto de cajetín (útil para presupuestos y medidas).
- Fotos y renders: sin fondo. Usa `python3 herramientas/sinfondo.py entrada.jpg salida.png [aspecto] [centro]` (fondo blanco y sombras a transparente, pieza opaca, recortado y centrado; para portadas usa aspecto 1.3333 y `centro`). Máximo 2000 px; Astro los convierte a WebP con transparencia.
- MIES: sin «papel» de nadie en el equipo; el resultado es solo el PDF de la lámina descargable (`public/proyectos/mies/`).
- Modelos de CATIA/SolidWorks: Martín exporta STEP (.stp) a la carpeta del proyecto; se convierte con `cascadio` (`pip install cascadio`; `cascadio.step_to_glb(stp, glb, tol_linear=0.1, tol_angular=0.5)`), se gira de Z arriba a Y arriba y se asignan materiales PBR (ojo: baseColorFactor va en espacio lineal). Ejemplo completo en `herramientas/mies_montar_modelos.py`.
- Un segundo visor 3D dentro del texto: `<figure class="visor-md"><model-viewer src="/modelos/x.glb" camera-controls ...></model-viewer><figcaption>…</figcaption></figure>` (solo funciona si el proyecto tiene `modelo`, que carga el script).
- Selector de versiones en el visor principal: en el frontmatter, `modeloVariantes: [{ nombre, src }]` y `etiquetaVariantes` (p. ej. «Balda»); `modelo` es la que sale al principio.
- Proyectos publicados: MIES (`mies`, 2026). Modelos: `mies-inferior/media/superior.glb` (módulo con cada tipo de balda, elegible en el visor) y `mies-pentagono.glb` (cada módulo con una balda distinta: inferior, media, superior, inferior, media). Scripts en `herramientas/mies_*.py`. El de ejemplo ya está borrado.

## Diseño
Concepto: hoja de plano técnico en «hormigón oscuro» (elegido por Martín): grises cálidos y un único acento amarillo señal #f2c14e (variable `--azul` por compatibilidad; apellido, enlaces, cotas, números de fase, botón principal). Fondo carbón #2a2927 que se funde en degradado con una banda algo más clara `--banda` #32312e (empieza al final de la portada, cubre la franja de las 5 fases de `Proceso.astro` y «Sobre mí», y vuelve al carbón antes de Contacto; sin cortes rectos), texto #efeeea, láminas y visores 3D sobre hormigón claro (`--lamina-fondo` #d8d7d3). La web es oscura siempre (no hay modo claro). Sin retícula ni cursor de coordenadas. Tipografía: Archivo Variable, jugando con su anchura. Mantén esta coherencia en los cambios.
- Logo: monograma «MT» (la pata derecha de la M es el palo de la T), amarillo sobre carbón. Está en `public/favicon.svg`, `public/apple-touch-icon.png` y en la cabecera (`Base.astro`, en línea con `currentColor`). En el móvil la cabecera muestra solo el monograma.
- Dibujos con líneas o texto negro: el nombre del archivo debe terminar en `-dibujo` (p. ej. `05-alzado-cotas-dibujo.png`) y se ponen solos sobre una hoja clara; los renders sin fondo van directamente sobre el carbón.

## Cuidado
- El repositorio es público: nada confidencial y ningún CAD original.
- El teléfono se ve en la web junto a los botones (Martín lo quiere visible), pero no está escrito en el HTML: se monta con JavaScript en `Contacto.astro`.
