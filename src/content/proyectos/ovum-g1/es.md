---
titulo: OVUM G-1
resumen: Gafas con una montura pensada para fabricarse con pasta de cáscara de huevo y alginato, cuya geometría sale de la optimización topológica. Para el concurso de diseño SILMO 2026.
anio: 2026
contexto: Concurso de diseño SILMO 2026
herramientas: [Autodesk Fusion, Blender, Impresión 3D SLA, Impresión 3D FDM]
equipo: [Óscar Ramón Mendiguchía, Nicolás Toribio González]
etiquetas: [Gafas, Diseño generativo, Optimización topológica, Biomateriales, Prototipado, Concurso]
portada: ./01-portada.png
portadaAlt: Montura OVUM G-1 de color hueso saliendo de una cáscara de huevo rota, con trozos de cáscara en el suelo
orden: 3
---

OVUM G-1 es nuestra propuesta para el concurso de diseño SILMO 2026, que pedía imaginar el futuro de unas gafas responsables. Nuestra respuesta fue convertir un residuo biológico, la cáscara de huevo, en una montura técnica y ergonómica, y dejar que fuera la propia estructura la que compensara las limitaciones del material.

## El reto y el material

La industria alimentaria desecha cáscara de huevo a escala industrial, aunque su composición mineral le da un potencial estructural real. El problema es que, como material compuesto, se lleva mal con las geometrías convencionales: aguanta bien a compresión, pero es frágil y resiste poco a tracción. Por eso el proyecto se planteó como una prueba: comprobar si el diseño estructural, por sí solo, podía hacer viable un material más débil y más limpio.

La pasta que proponemos mezcla polvo de cáscara de huevo y alginato, un aglutinante que se saca de las algas y que aporta algo de flexibilidad, sin polímeros derivados del petróleo. El acabado natural y granulado de la cáscara se queda a la vista, sin pinturas ni recubrimientos, así que el producto mantiene el vínculo con su origen. La pasta sigue siendo una propuesta en desarrollo: los prototipos físicos que hicimos fueron de resina y de PLA, como se explica más abajo.

## Bocetos

Resolvimos en papel las restricciones geométricas principales (el frontal envolvente, el puente nasal y la forma de las patillas) antes de pasar al 3D, ya que así evitábamos ir probando a ciegas en el CAD y rehacer trabajo. El modelo final se parece mucho a estos primeros bocetos.

![Bocetos a mano de las gafas: vista en perspectiva, frontal y de la patilla calada](./02-bocetos-dibujo.png)
![Bocetos de la patilla con los vaciados de la estructura](./03-bocetos-perfil-dibujo.png)
*Bocetos iniciales del frontal y evolución de la patilla calada.*

## Modelado en Fusion

Modelamos la montura en Autodesk Fusion con modelado de forma libre, parecido al modelado de superficies de SolidWorks. Así pudimos pasar de una forma orgánica y ergonómica a un sólido cerrado y calculable, listo para la optimización topológica.

![Frontal de la montura modelado en Fusion, con el puente nasal](./04-fusion-frontal.png)
![Vista lateral del modelo base en Fusion](./05-fusion-lateral.png)
![Arranque de la patilla con el alojamiento de la bisagra](./06-fusion-patilla.png)
*Modelo base en Fusion: frontal, perfil y arranque de la patilla.*

## Bisagra y puente

**Bisagra sin tornillos.** Es una bisagra puramente geométrica, pensada para resistir bien a cortante y para absorber las cargas repetidas de abrir y cerrar sin dañar el material orgánico. Pliega con suavidad y tiene un tope estricto a 115°.

![Despiece de la bisagra entre el frontal y la patilla](./07-bisagra-despiece.png)
![Bisagra montada](./08-bisagra-montada.png)
![Patilla en Fusion con el pasador de la bisagra](./08b-bisagra-pasador.jpg)
*Bisagra entre frontal y patilla: despiece, montaje y pasador.*

**Puentes intercambiables.** El puente nasal se cambia para ajustar la comodidad y el reparto del peso a cada cara. Se fija con un pasador hexagonal que bloquea el ángulo exacto, sin holguras y sin tornillos. Las lentes también encajan a presión desde la base del frontal, así que montarlas o cambiarlas es rápido.

![Frontal con el puente nasal intercambiable](./09-puente.png)
*Frontal con el puente nasal intercambiable.*

La forma envolvente del frontal amplía la visión periférica, el puente reparte la presión sobre la nariz y la montura lleva canales de ventilación y zonas de agarre para que no se mueva.

![Esquema de ergonomía: vistas frontal y lateral con flechas de ventilación y apoyo](./09b-ergonomia-dibujo.png)
*Ergonomía: ventilación, visión periférica y apoyo de la montura.*

## Diseño generativo

Para las patillas usamos el diseño generativo y la optimización topológica de Fusion con dos objetivos a la vez: gastar el mínimo de material bajo carga y alejar las tensiones de las zonas donde suelen romper los compuestos biominerales frágiles. Primero definimos las geometrías que había que conservar (los puntos de anclaje, en verde) y las zonas que debían quedar libres (en rojo). Después aplicamos las fuerzas y las restricciones reales y metimos la densidad y el límite elástico del material, y el algoritmo generó una malla optimizada y ligera.

![Geometrías de conservación en verde y de obstáculo en rojo sobre la patilla](./10-geometrias.png)
![Análisis por elementos finitos de la patilla optimizada](./11-fea.jpg)
*Geometrías de conservación y obstáculo, y análisis por elementos finitos de la patilla.*

El resultado imita estructuras naturales, como el hueso trabecular o las redes de micelio. No es un recurso estético, sino que se quita material donde la tensión es baja, de modo que la patilla queda muy rígida y con mucha menos masa. El engrosamiento en las uniones y el esqueleto del puente y las patillas son la expresión geométrica de los límites del material, y el aspecto brutalista viene de dejar esa lógica a la vista.

![Patilla con los vaciados de la optimización topológica](./12-patilla-optimizada.png)
*Patilla optimizada.*

Con el modelo cerrado, comprobamos las interferencias y validamos todas las tolerancias para asegurar que las piezas encajaran bien en físico.

![Despiece del frontal y la patilla optimizada](./13-despiece-generativo.png)
![Vista lateral del conjunto montado](./14-conjunto-lateral.png)
![Perspectiva del conjunto montado](./15-conjunto-perspectiva.png)
*Conjunto final: despiece, vista lateral y perspectiva.*

![Planos con cotas: frontal de 152,76 mm, perfil de 164,65 mm, planta de 153,06 por 156,49 mm y detalle de las piezas que encajan](./24-cotas-dibujo.png)
*Medidas generales en mm y detalle de las piezas que encajan entre sí.*

## Render

Con el diseño mecánico cerrado, llevamos la malla a Blender, simulamos la textura de la biocerámica de cáscara de huevo y preparamos la iluminación de estudio para los renders finales.

![Escena de Blender con la cámara y las luces de estudio](./16-blender-modelo.jpg)
![Nodos del material de cáscara de huevo en Blender](./16b-blender-material.jpg)
*Escena y material en Blender.*

![Render lateral de la montura con textura de cáscara de huevo](./17-render-lateral.png)
![Render en perspectiva de la montura](./19-render-perspectiva.png)
*Renders con el acabado granulado de la cáscara.*

![Detalle de la bisagra con la textura porosa del material](./18-render-detalle.png)
*Detalle de la bisagra.*

## Prototipos

**Resina SLA.** Imprimimos un prototipo a 0,05 mm en una impresora de resina Anycubic solo para valorar cómo se veía la malla generativa. Como la resina estándar se deforma y se degrada con la luz ultravioleta, este modelo sirvió para revisar la forma y no para ensayos mecánicos.

![Prototipo de resina gris sobre la mesa de corte](./20-sla-a.jpg)
![Piezas de resina recién impresas en la cesta de lavado](./20-sla-b.jpg)
![Montura de resina montada sobre la mesa](./20-sla-c.jpg)
*Prototipo en resina SLA para revisar la forma.*

**PLA en FDM.** Imprimimos un segundo modelo en PLA en una Bambu Lab A1 dedicado por completo a las pruebas estructurales: el rozamiento de las bisagras, los topes de giro y las tolerancias de montaje.

![Patillas y frontal de PLA sobre la cama de la impresora](./21-fdm-a.jpg)
![Frontal de PLA recién impreso en la Bambu Lab A1](./21-fdm-b.jpg)
![Patilla de PLA con los vaciados](./21-fdm-c.jpg)
*Prototipo en PLA para probar bisagras y tolerancias.*

Pintamos el prototipo de PLA y no el de resina a propósito: las irregularidades y la microtextura de la impresión FDM, una vez pintadas, imitaban muy bien el acabado poroso y granulado que tendría la biocerámica de cáscara de huevo.

![Montura de PLA pintada en color hueso, vista en perspectiva](./22-pintado-b.jpg)
![Patillas y puente pintados en el taller](./22-pintado-a.jpg)
![Montura pintada vista de frente](./22-pintado-c.jpg)
*Prototipo de PLA pintado con el acabado de la cáscara.*

## Validación ergonómica

Para contrastar los datos digitales con la realidad, probamos las gafas en varias personas y comprobamos que la montura y los puentes intercambiables se ajustaban bien a caras reales, sin puntos de presión y sin moverse.

![Dos personas probándose el prototipo blanco con el puente gris](./23-ergonomia-a.jpg)
*Pruebas del prototipo en caras reales.*

![Primer plano de una chica con el prototipo puesto](./23-ergonomia-c.jpg)
*Ajuste del puente nasal sobre la nariz.*

![Chico de perfil con el prototipo pintado puesto](./23-ergonomia-b.jpg)
*Prototipo pintado puesto, de perfil.*

## Estuche

Completamos la propuesta con un estuche en forma de cápsula, también modelado en Fusion.

![Estuche en forma de cápsula con las gafas dentro, modelado en Fusion](./25-estuche.jpg)
*Estuche modelado en Fusion.*

## Paneles de entrega

<a class="boton boton--lleno" href="/proyectos/ovum-g1/OVUM-G1-paneles.pdf" download>Descargar los paneles (PDF, 1,5 MB)</a>
