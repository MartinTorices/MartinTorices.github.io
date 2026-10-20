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
});
