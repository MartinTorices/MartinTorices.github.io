// @ts-check
import { defineConfig } from 'astro/config';

// Configuración general de la web.
// "site" es la dirección pública donde se publica (GitHub Pages).
export default defineConfig({
  site: 'https://martintorices.github.io',
  trailingSlash: 'always',
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  // Calidad de las imágenes (renders y fotos): WebP al 92 % (por defecto, 80),
  // color más fino en los bordes y transparencia sin pérdida
  image: {
    service: {
      entrypoint: 'astro/assets/services/sharp',
      config: { webp: { quality: 92, alphaQuality: 100, smartSubsample: true, effort: 6 } },
    },
  },
});
