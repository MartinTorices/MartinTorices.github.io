---
titulo: MIES
resumen: Mobiliario expositivo modular de contrachapado de chopo y aluminio, inspirado en las espigas de cereal, para el concurso «Proyecto de Cátedra» de AEICE y la ETSAVA.
anio: 2026
contexto: Concurso «Proyecto de Cátedra» AEICE y ETSAVA
herramientas: [CATIA V5, Adobe Illustrator]
equipo: [Óscar Ramón Mendiguchía, Nicolás Toribio González]
rol: Diseño
etiquetas: [Diseño modular, Mobiliario expositivo, Madera y aluminio, Concurso]
portada: ./01-portada-zigzag.jpg
portadaAlt: Varios módulos MIES unidos en zigzag, con baldas de contrachapado y perfiles de aluminio ahusados
orden: 1
---

## El encargo

AEICE, el Clúster de Hábitat Eficiente de Castilla y León, y la Escuela de Arquitectura de Valladolid (ETSAVA) convocaron en diciembre de 2025 un concurso para diseñar un elemento expositivo modular, desmontable y transportable con el que exponer los trabajos de los estudiantes de la Universidad de Valladolid.

MIES es un proyecto conjunto con Óscar Ramón Mendiguchía y Nicolás Toribio González, en el que me encargué del diseño. La entrega, el 26 de enero de 2026, fue una lámina A1 y un presupuesto de fabricación.

## Concepto

> Mies. Cereal maduro listo para ser segado, base del paisaje castellano.

El proyecto parte de una inversión: la fragilidad de las espigas se convierte en vigas de aluminio que se agrupan en bloque, como el cereal. El nombre también juega con un segundo sentido, el de una arquitectura de claridad material y estructural en la que «menos es más». La propuesta une un recurso forestal de Castilla y León, el contrachapado de chopo, con la precisión industrial del aluminio.

## Diseño y CAD

Cada módulo tiene una base y tres baldas de contrachapado de chopo con forma de trapecio y cuatro perfiles de aluminio en L, de 2,10 m de alto, que se estrechan de 76 a 20 mm. Por eso cada balda lleva ranuras de un tamaño distinto (60, 49 y 37 mm) y se queda encajada a su altura sin herrajes: al encajar, las propias baldas forman la estructura.

![Un módulo MIES montado, con la base, tres baldas y cuatro perfiles de aluminio](./03-modulo.jpg)
![Alzado acotado del módulo, con la altura de cada balda](./05-alzado-cotas.jpg)
*Módulo montado y alzado acotado: 2.100 mm de altura, con las baldas a 600, 1.050 y 1.600 mm.*

Los lados del trapecio forman 36° con la vertical, así que cinco módulos cierran un pentágono. El modelo y los planos para el corte CNC se hicieron en CATIA V5.

![Plano acotado de la base del módulo, en forma de trapecio](./08-plano-base.jpg)
*Plano de la base: trapecio de 300 mm de fondo, lado corto de 600 mm y lados a 36°.*

![Plano de la balda inferior B.3](./plano-balda-B3.svg)
![Plano de la balda media B.2](./plano-balda-B2.svg)
![Plano de la balda superior B.1](./plano-balda-B1.svg)
*Planos de las baldas B.3, B.2 y B.1 exportados de CATIA: las ranuras pasan de 60 a 49 y a 37 mm según la altura.*

## Agrupaciones

En círculo, los módulos crean zonas de reunión abiertas para charlar en grupo viéndose las caras; en zigzag, la estructura se estira para acompañar las zonas de paso; y las configuraciones abiertas forman pequeños refugios que dividen el espacio de forma suave. Las perforaciones de los perfiles permiten tensar cuerdas para colgar paneles en formato A1.

![Cinco módulos MIES cerrando un pentágono](./02-agrupacion-pentagono.jpg)
![Esquemas en planta de las agrupaciones en pentágono, zigzag y abiertas](./06-agrupaciones.jpg)
*Agrupación en pentágono y esquemas en planta de las distintas configuraciones.*

## Montaje y transporte

Primero se asienta la base para dar estabilidad, después se encajan los perfiles que forman el esqueleto y, con el bastidor levantado, se colocan las baldas de abajo arriba.

![Despiece del módulo: base, tres baldas y cuatro perfiles](./04-despiece.jpg)
*Despiece: base, tres baldas y cuatro perfiles de aluminio.*

Cada módulo viaja en una bolsa de rafia agrícola reciclada, fiel al origen del material, con asas para cargarla entre dos personas, de modo que la instalación es un esfuerzo compartido desde el principio.

![Dos personas cargando el módulo dentro de una bolsa de rafia reciclada](./07-packaging.jpg)
*Embalaje en bolsa de rafia reciclada.*

## Materiales y presupuesto

Contrachapado de chopo de 25 mm, ligado a la industria forestal de Castilla y León, y chapa de aluminio 5052 H32 de 5 mm cortada y plegada. Junto con la lámina entregamos un presupuesto de fabricación:

| Presupuesto (IVA incluido, con retención de IRPF) | Total |
| --- | --- |
| Prototipo, 1 módulo | 1.015,48 € |
| Conjunto de 5 módulos | 2.385,00 € |
| Serie de 10 módulos (estimación) | unos 4.000 € |

Al fabricar en serie, el coste por módulo baja de 1.015 € a unos 400 €, gracias a la compra por volumen, al aprovechamiento del tablero en el corte CNC (nesting) y al reparto de los costes fijos de programación y transporte.

## Resultado

MIES no resultó premiado y no llegó a fabricarse, pero el diseño quedó definido hasta los planos de fabricación y el presupuesto.

![Lámina A1 completa de la entrega del proyecto MIES](./09-lamina-A1-completa.jpg)
*Lámina A1 de la entrega. [Ver la lámina a tamaño completo](/proyectos/mies/MIES-lamina-A1.jpg)*
