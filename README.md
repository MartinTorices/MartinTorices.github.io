# Porfolio de Martín Torices

Web de porfolio hecha con [Astro](https://astro.build) y publicada gratis en GitHub Pages:
**https://martintorices.github.io**

## Dónde está cada cosa

| Quiero cambiar… | Archivo |
| --- | --- |
| Correo, LinkedIn, teléfono, CV, programas | `src/config.ts` |
| Texto de «Sobre mí» (ES y EN) | `src/config.ts` → `sobreMi` |
| Textos fijos de la web (menús, botones) | `src/i18n.ts` |
| Colores y tipografía | `src/styles/global.css` (arriba del todo) |
| Un proyecto | `src/content/proyectos/<nombre-del-proyecto>/` |
| Modelos 3D (.glb) | `public/modelos/` |
| CV en PDF | `public/cv/` |

## Cómo añadir un proyecto

1. Crea una carpeta en `src/content/proyectos/`, con un nombre corto sin espacios ni tildes
   (por ejemplo `lampara-flexo`). Ese nombre será la dirección: `/proyectos/lampara-flexo/`.
2. Dentro, pon la imagen de portada y el resto de imágenes (JPG o PNG; la web las optimiza sola).
3. Copia `es.md` y `en.md` del proyecto de ejemplo y cambia los datos de arriba:
   - `titulo`, `resumen`, `anio`, `contexto` (asignatura, concurso…), `herramientas`
   - `portada` y `portadaAlt` (descripción de la imagen para accesibilidad)
   - `modelo`: ruta del .glb, por ejemplo `/modelos/lampara-flexo.glb` (opcional)
   - `orden`: número menor = sale antes. `borrador: true` = no se publica.
4. Escribe el caso de estudio debajo. Cada `## Título` es una fase numerada
   (problema, bocetos, CAD, prototipo, resultado). Las imágenes se ponen así:
   `![Descripción](./boceto-1.jpg)`
5. Guarda el modelo 3D en `public/modelos/` (mejor por debajo de 10 MB).

### Exportar el modelo 3D desde SolidWorks

Archivo → Guardar como → tipo *Extended Reality (\*.glb)*. Si pesa mucho, se puede simplificar.
Ojo: el .glb es descargable por cualquiera. No subas nada confidencial.

## Probar la web en el ordenador (opcional)

Requiere [Node.js](https://nodejs.org) 22 o superior.

```bash
npm install
npm run dev      # abre http://localhost:4321
npm run build    # genera la web final en dist/
```

## Publicar

Cada vez que se suben cambios a la rama `main` de GitHub, la web se compila y se publica sola
(`.github/workflows/deploy.yml`). Tarda uno o dos minutos.
