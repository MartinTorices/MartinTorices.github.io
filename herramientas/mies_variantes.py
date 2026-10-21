import trimesh, numpy as np, sys
sys.path.insert(0,'.')
from mies_montar_modelos import piezas, escena
d="expositor_tabla_"
inf=piezas(d+"inferior.glb"); med=piezas(d+"media.glb"); sup=piezas(d+"superior.glb")
for m in med: m[1].apply_translation([0,0,1.2])   # misma referencia que las otras dos
out="/home/claude/martintorices.github.io/public/modelos/"
for nombre,lista in [("inferior",inf),("media",med),("superior",sup)]:
    escena([(n if not n.startswith("Part2") else "balda",m) for n,m in lista]).export(out+f"mies-{nombre}.glb")
# pentágono: cada módulo con una balda distinta (inferior, media, superior, inferior, media)
pen=piezas("expositor_todopentagono.glb")
ref=dict(pen)["base.1_4"]
balda={ "inferior":[m for n,m in inf if n.startswith("Part2")][0], "media":[m for n,m in med if n.startswith("Part2")][0], "superior":[m for n,m in sup if n.startswith("Part2")][0]}
for k in balda: balda[k]=balda[k].copy(); balda[k].apply_translation([0,0,-1.2])  # al marco del pentágono
sufijos=sorted({n.split(".1")[-1] for n,_ in pen if n.startswith("base")})  # '', '_1'..'_4'
orden=["inferior","media","superior","inferior","media"]
lista=[(n,m) for n,m in pen if not n.startswith("Part2")]
for i,suf in enumerate(sufijos):
    base=dict(pen)["base.1"+suf]
    M,_,c=trimesh.registration.procrustes(ref.vertices,base.vertices,reflection=False,scale=False,return_cost=True)
    b=balda[orden[i]].copy(); b.apply_transform(M); lista.append((f"balda_{orden[i]}{suf}",b))
escena(lista).export(out+"mies-pentagono.glb")
import os
for f in ["mies-inferior","mies-media","mies-superior","mies-pentagono"]:
    s=trimesh.load(out+f+".glb"); print(f, os.path.getsize(out+f+".glb")//1024,"KB",(s.extents*1000).round().tolist(), len(s.geometry))
