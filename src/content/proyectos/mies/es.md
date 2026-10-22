---
titulo: MIES
resumen: Mobiliario expositivo modular de contrachapado de chopo y aluminio, inspirado en las espigas de cereal, para el concurso «Proyecto de Cátedra» de AEICE y la ETSAVA.
anio: 2026
contexto: Concurso «Proyecto de Cátedra» AEICE y ETSAVA
herramientas: [CATIA V5, Adobe Illustrator]
equipo: [Óscar Ramón Mendiguchía, Nicolás Toribio González]
etiquetas: [Diseño modular, Mobiliario expositivo, Madera y aluminio, Concurso]
portada: ./01-portada-zigzag.png
portadaAlt: Varios módulos MIES unidos en zigzag, con baldas de contrachapado y perfiles de aluminio ahusados
modelo: /modelos/mies-inferior.glb
etiquetaVariantes: Balda
modeloVariantes:
  - { nombre: Inferior, src: /modelos/mies-inferior.glb }
  - { nombre: Media, src: /modelos/mies-media.glb }
  - { nombre: Superior, src: /modelos/mies-superior.glb }
orden: 1
---

MIES es un proyecto para el concurso «Proyecto de Cátedra» que convocaron AEICE, el Clúster de Hábitat Eficiente de Castilla y León, y la Escuela de Arquitectura de Valladolid (ETSAVA) en diciembre de 2025. Se pedía un elemento expositivo modular, desmontable y transportable para exponer los trabajos de los estudiantes de la Universidad de Valladolid, y la entrega, el 26 de enero de 2026, fue una lámina A1 y un presupuesto de fabricación.

## Concepto

> Mies. Cereal maduro listo para ser segado, base del paisaje castellano.

El proyecto parte de una inversión: la fragilidad de las espigas se convierte en vigas de aluminio que se agrupan en bloque, como el cereal. El nombre también juega con un segundo sentido, el de una arquitectura de claridad material y estructural en la que «menos es más». La propuesta une un recurso forestal de Castilla y León, el contrachapado de chopo, con la precisión industrial del aluminio.

## Diseño y CAD

Cada módulo tiene una base y tres baldas de contrachapado de chopo con forma de trapecio y cuatro perfiles de aluminio en L, de 2,10 m de alto, que se estrechan de 76 a 20 mm. Por eso cada balda lleva ranuras de un tamaño distinto (60, 49 y 37 mm) y se queda encajada a su altura sin herrajes: al encajar, las propias baldas forman la estructura.

![Un módulo MIES montado, con la base, tres baldas y cuatro perfiles de aluminio](./03-modulo.png)
![Alzado acotado del módulo, con la altura de cada balda](./05-alzado-cotas-dibujo.png)
*Módulo montado y alzado acotado: 2.100 mm de altura, con las baldas a 600, 1.050 y 1.600 mm.*

Los lados del trapecio forman 36° con la vertical, así que cinco módulos cierran un pentágono. El modelo y los planos para el corte CNC se hicieron en CATIA V5.

## Agrupaciones

En círculo, los módulos crean zonas de reunión abiertas para charlar en grupo viéndose las caras; en zigzag, la estructura se estira para acompañar las zonas de paso; y las configuraciones abiertas forman pequeños refugios que dividen el espacio de forma suave. Las perforaciones de los perfiles permiten tensar cuerdas para colgar paneles en formato A1.

![Cinco módulos MIES cerrando un pentágono](./02-agrupacion-pentagono.png)
![Esquemas en planta de las agrupaciones en pentágono, zigzag y abiertas](./06-agrupaciones-dibujo.png)
*Agrupación en pentágono y esquemas en planta de las distintas configuraciones.*

![Otra vista de cinco módulos MIES en pentágono](./08-pentagono-otra-vista.png)
![Agrupación abierta de módulos MIES](./09-agrupacion-abierta.png)
*Otra vista del pentágono y agrupación abierta.*

<figure class="visor-md">
<model-viewer src="/modelos/mies-pentagono.glb" alt="Cinco módulos MIES cerrando un pentágono, en 3D" camera-controls touch-action="pan-y" auto-rotate auto-rotate-delay="1500" rotation-per-second="14deg" interaction-prompt="none" camera-orbit="112deg 68deg auto" shadow-intensity="0.85" shadow-softness="0.75" exposure="1" tone-mapping="neutral" environment-image="/modelos/estudio.hdr" ar ar-modes="webxr scene-viewer quick-look"><button slot="ar-button" class="boton visor-md__ar">Ver en tu espacio (AR)</button></model-viewer>
<figcaption>Agrupación en pentágono en 3D, montada como en una exposición: una balda distinta en cada módulo con maquetas, láminas A1 colgadas al fondo de cuerdas que pasan por las perforaciones de los perfiles y una figura de 1,75 m para ver la escala. Arrastra para girarla o, en el móvil, ponla en tu espacio con el botón de realidad aumentada.</figcaption>
</figure>

## Montaje y transporte

Primero se asienta la base para dar estabilidad, después se encajan los perfiles que forman el esqueleto y, con el bastidor levantado, se colocan las baldas de abajo arriba.

![Despiece del módulo: base, tres baldas y cuatro perfiles](./04-despiece.png)
*Despiece: base, tres baldas y cuatro perfiles de aluminio.*

Cada módulo viaja en una bolsa de rafia agrícola reciclada, fiel al origen del material, con asas para cargarla entre dos personas, de modo que la instalación es un esfuerzo compartido desde el principio.

![Dos personas cargando el módulo dentro de una bolsa de rafia reciclada](./07-packaging-dibujo.png)
*Embalaje en bolsa de rafia reciclada.*

## Materiales y presupuesto

Contrachapado de chopo de 25 mm, ligado a la industria forestal de Castilla y León, y chapa de aluminio 5052 H32 de 5 mm cortada y plegada. Junto con la lámina entregamos un presupuesto de fabricación:

| Presupuesto (IVA incluido, con retención de IRPF) | Total |
| --- | --- |
| Prototipo, 1 módulo | 1.015,48 € |
| Conjunto de 5 módulos | 2.385,00 € |
| Serie de 10 módulos (estimación) | unos 4.000 € |

*Datos orientativos, calculados en enero de 2026, cuando se hizo el diseño.*

Al fabricar en serie, el coste por módulo baja de 1.015 € a unos 400 €, gracias a la compra por volumen, al aprovechamiento del tablero en el corte CNC (nesting) y al reparto de los costes fijos de programación y transporte.

## Lámina de entrega

<a class="boton boton--lleno" href="/proyectos/mies/MIES-lamina-A1.pdf" download>Descargar la lámina A1 (PDF, 1,5 MB)</a>
