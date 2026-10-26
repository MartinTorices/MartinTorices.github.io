---
titulo: OVUM G-1
resumen: Eyewear whose frame is designed to be made from an eggshell and alginate paste, with a geometry driven by topology optimisation. For the SILMO 2026 design contest.
anio: 2026
contexto: SILMO 2026 design contest
herramientas: [Autodesk Fusion, Blender, SLA 3D printing, FDM 3D printing]
equipo: [Óscar Ramón Mendiguchía, Nicolás Toribio González]
etiquetas: [Eyewear, Generative design, Topology optimisation, Biomaterials, Prototyping, Competition]
portada: ./01-portada.png
portadaAlt: Bone-coloured OVUM G-1 frame emerging from a broken eggshell, with shell fragments on the floor
modelo: /modelos/ovum-g1.glb
modeloAlt: "3D model of the OVUM G-1 glasses with an eggshell finish: front, nose bridge and two perforated temples"
etiquetaVariantes: View
modeloVariantes:
  - { nombre: Assembled, src: /modelos/ovum-g1.glb }
  - { nombre: Exploded, src: /modelos/ovum-g1-montaje.glb }
orden: 3
---

OVUM G-1 is our proposal for the SILMO 2026 design contest, which asked for a look into the future of responsible eyewear. Our answer was to turn a biological waste, eggshell, into a technical and ergonomic frame, and to let the structure itself make up for the limits of the material.

<figure class="video-md">
  <video controls playsinline preload="metadata" poster="/proyectos/ovum-g1/OVUM-G1-video-poster.jpg">
    <source src="/proyectos/ovum-g1/OVUM-G1-video.mp4" type="video/mp4">
  </video>
  <figcaption>OVUM G-1 presentation video (56 s), animated in Blender.</figcaption>
</figure>

In the 3D viewer above you can rotate the glasses, zoom in to see the eggshell texture and, in the «Exploded» view, watch the front, the nose bridge and the temples come apart and click back together.

## The challenge and the material

The food industry throws away eggshell on an industrial scale, even though its mineral composition gives it real structural potential. The problem is that, as a composite, it does not suit conventional geometries: it performs well in compression but is brittle and weak in tension. So the project was set up as a test: could structural design alone make a weaker, cleaner material viable?

The paste we propose mixes eggshell powder with alginate, a seaweed-derived binder that adds some flexibility, with no petroleum-based polymers. The natural, grainy finish of the shell is left visible, with no paint or coatings, so the product keeps a direct link to its origin. The paste is still a proposal under development: the physical prototypes we made were in resin and PLA, as explained below.

## Sketches

We solved the main geometric constraints on paper (the wraparound front, the nose bridge and the shape of the temples) before moving to 3D, which saved us from blind iteration and rework in CAD. The final model stays very close to these first sketches.

![Hand sketches of the glasses: perspective, front view and the perforated temple](./02-bocetos-dibujo.png)
![Sketches of the temple with the structural cut-outs](./03-bocetos-perfil-dibujo.png)
*Early sketches of the front and evolution of the perforated temple.*

## Modelling in Fusion

We modelled the frame in Autodesk Fusion with freeform modelling, similar to surface modelling in SolidWorks. This let us go from an organic, ergonomic shape to a closed, calculable solid ready for topology optimisation.

![Frame front modelled in Fusion, with the nose bridge](./04-fusion-frontal.png)
![Side view of the base model in Fusion](./05-fusion-lateral.png)
![Start of the temple with the hinge housing](./06-fusion-patilla.png)
*Base model in Fusion: front, side and start of the temple.*

## Hinge and bridge

**Screwless hinge.** It is a purely geometric hinge, designed for high shear strength and to absorb the repeated loads of opening and closing without damaging the organic material. It folds smoothly and has a strict 115° stop.

![Exploded view of the hinge between front and temple](./07-bisagra-despiece.png)
![Assembled hinge](./08-bisagra-montada.png)
![Temple in Fusion with the hinge pin](./08b-bisagra-pasador.jpg)
*Hinge between front and temple: exploded view, assembly and pin.*

**Interchangeable bridges.** The nose bridge can be swapped to adjust comfort and weight balance to each face. It is fixed with a hexagonal pin that locks the exact angle, with no wobble and no screws. The lenses also snap in from the base of the front, so fitting or replacing them is quick.

![Front with the interchangeable nose bridge](./09-puente.png)
*Front with the interchangeable nose bridge.*

The wraparound front widens peripheral vision, the bridge spreads the pressure on the nose, and the frame includes ventilation channels and grip areas so it stays in place.

![Ergonomics diagram: front and side views with ventilation and support arrows](./09b-ergonomia-dibujo.png)
*Ergonomics: ventilation, peripheral vision and support of the frame.*

## Generative design

For the temples we used Fusion's generative design and topology optimisation with two goals at once: using as little material as possible under load and moving stress away from the areas where brittle biomineral composites usually fail. First we defined the geometry to preserve (the anchor points, in green) and the areas that had to stay clear (in red). Then we applied the real forces and constraints and entered the material's density and yield strength, and the algorithm produced an optimised, lightweight mesh.

![Preserve geometry in green and obstacle geometry in red on the temple](./10-geometrias.png)
![Finite element analysis of the optimised temple](./11-fea.jpg)
*Preserve and obstacle geometry, and finite element analysis of the temple.*

The result echoes natural structures such as trabecular bone or mycelium networks. It is not an aesthetic choice: material is removed where stress is low, so the temple stays very stiff with much less mass. The thicker joints and the skeleton of the bridge and temples are the geometric expression of the material's limits, and the brutalist look comes from keeping that logic visible.

![Temple with the cut-outs from topology optimisation](./12-patilla-optimizada.png)
*Optimised temple.*

Once the model was locked, we ran interference checks and validated every tolerance to make sure the parts would fit together physically.

![Exploded view of the front and the optimised temple](./13-despiece-generativo.png)
![Side view of the assembled frame](./14-conjunto-lateral.png)
![Perspective of the assembled frame](./15-conjunto-perspectiva.png)
*Final assembly: exploded view, side view and perspective.*

![Dimensioned drawings: 152.76 mm front, 164.65 mm side, 153.06 by 156.49 mm top view and detail of the interlocking parts](./24-cotas-dibujo.png)
*Overall dimensions in mm and detail of the interlocking parts.*

## Rendering

With the mechanical design finished, we brought the mesh into Blender, simulated the texture of the eggshell bioceramic and set up the studio lighting for the final renders.

![Blender scene with the camera and studio lights](./16-blender-modelo.jpg)
![Eggshell material nodes in Blender](./16b-blender-material.jpg)
*Scene and material in Blender.*

![Side render of the frame with eggshell texture](./17-render-lateral.png)
![Perspective render of the frame](./19-render-perspectiva.png)
*Renders with the grainy eggshell finish.*

![Detail of the hinge with the porous texture of the material](./18-render-detalle.png)
*Hinge detail.*

## Prototypes

**SLA resin.** We printed a 0.05 mm prototype on an Anycubic resin printer purely to judge how the generative mesh looked. Since standard resin warps and degrades under UV light, this model was used for form review, not for mechanical testing.

![Grey resin prototype on the cutting mat](./20-sla-a.jpg)
![Freshly printed resin parts in the washing basket](./20-sla-b.jpg)
![Assembled resin frame on the table](./20-sla-c.jpg)
*SLA resin prototype for form review.*

**FDM PLA.** We printed a second model in PLA on a Bambu Lab A1, entirely for structural testing: hinge friction, angle stops and assembly tolerances.

![PLA temples and front on the printer bed](./21-fdm-a.jpg)
![PLA front freshly printed on the Bambu Lab A1](./21-fdm-b.jpg)
![PLA temple with the cut-outs](./21-fdm-c.jpg)
*PLA prototype for testing hinges and tolerances.*

We deliberately painted the PLA prototype rather than the resin one: once painted, the irregularities and micro-texture of the FDM print closely imitated the porous, grainy finish the eggshell bioceramic would have.

![PLA frame painted bone colour, in perspective](./22-pintado-b.jpg)
![Painted temples and bridge in the workshop](./22-pintado-a.jpg)
![Painted frame seen from the front](./22-pintado-c.jpg)
*PLA prototype painted with the eggshell finish.*

## Ergonomic validation

To check our digital data against reality, we tried the glasses on several people and confirmed that the frame and the interchangeable bridges sat well on real faces, with no pressure points and no wobble.

![Two people trying on the white prototype with the grey bridge](./23-ergonomia-a.jpg)
*Testing the prototype on real faces.*

![Close-up of a young woman wearing the prototype](./23-ergonomia-c.jpg)
*Fit of the nose bridge.*

![Young man in profile wearing the painted prototype](./23-ergonomia-b.jpg)
*Painted prototype worn, in profile.*

## Case

We completed the proposal with a capsule-shaped case, also modelled in Fusion.

![Capsule-shaped case with the glasses inside, modelled in Fusion](./25-estuche.jpg)
*Case modelled in Fusion.*

## Submission boards

<a class="boton boton--lleno" href="/proyectos/ovum-g1/OVUM-G1-paneles.pdf" download>Download the boards (PDF, 1.5 MB)</a>
