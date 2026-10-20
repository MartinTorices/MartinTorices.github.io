// ============================================================
//  DATOS PERSONALES DE LA WEB
//  Cambia aquí tu información: se actualiza en toda la web.
// ============================================================

export const persona = {
  nombre: 'Martín Torices Sarmentero',
  nombreCorto: 'Martín Torices',
  correo: 'martintoricess@gmail.com',
  linkedin: 'https://www.linkedin.com/in/martintorices',
  // El teléfono va troceado para que los robots no lo lean de un vistazo.
  // Se monta en el navegador al pulsar «Llamar» o «WhatsApp».
  telefono: { prefijo: '34', partes: ['696', '997', '657'] },
  // Ruta del CV dentro de /public. Déjalo en null hasta tener el PDF:
  // mientras sea null, el botón de descarga no aparece.
  cv: null as string | null, // ejemplo: '/cv/CV-Martin-Torices.pdf'
  // Programas que aparecen en «Sobre mí»
  programas: ['CATIA', 'SolidWorks'],
};

export const estudios = {
  es: {
    titulacion: 'Ingeniería de Diseño Industrial y Desarrollo del Producto',
    curso: '4.º curso',
    centro: 'Escuela de Ingenierías Industriales, Universidad de Valladolid',
  },
  en: {
    titulacion: 'Industrial Design and Product Development Engineering',
    curso: '4th year',
    centro: 'School of Industrial Engineering, University of Valladolid',
  },
};

// Texto de «Sobre mí». Cada elemento de la lista es un párrafo.
export const sobreMi = {
  es: [
    'Soy Martín Torices, estudiante de 4.º de Ingeniería de Diseño Industrial y Desarrollo del Producto en la Escuela de Ingenierías Industriales de la Universidad de Valladolid.',
    'Apasionado por todo el camino del diseño, desde la idea y los primeros bocetos hasta el modelo en CAD y el prototipo, e interesado también por cómo se lleva a cabo cada producto en la fase de producción. Por eso, en este porfolio cuento cada proyecto paso a paso.',
    'Tengo experiencia en programas de diseño como CATIA y SolidWorks, entre otros.',
  ],
  en: [
    "I'm Martín Torices, a fourth-year Industrial Design and Product Development Engineering student at the School of Industrial Engineering of the University of Valladolid.",
    "I'm passionate about the whole design journey, from the first idea and sketches to the CAD model and the prototype, and also interested in how each product is brought to life in the production phase. That's why this portfolio walks through every project step by step.",
    'I have experience with design software such as CATIA and SolidWorks, among others.',
  ],
};
