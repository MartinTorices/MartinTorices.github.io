import trimesh, numpy as np
from trimesh.visual.material import PBRMaterial
def piezas(path):
    s=trimesh.load(path); out=[]
    for node in s.graph.nodes_geometry:
        T,g=s.graph[node]; m=s.geometry[g].copy(); m.apply_transform(T); out.append((node,m))
    return out
def mat(nombre):
    if nombre.startswith("Part1"):  # perfiles de aluminio
        return PBRMaterial(name="aluminio",baseColorFactor=[38,40,44,255],metallicFactor=0.75,roughnessFactor=0.38)
    return PBRMaterial(name="chopo",baseColorFactor=[147,96,48,255],metallicFactor=0.0,roughnessFactor=0.78)
def escena(lista):
    sc=trimesh.Scene()
    Rx=trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0])  # Z arriba -> Y arriba (glTF)
    for i,(n,m) in enumerate(lista):
        m=m.copy(); m.apply_transform(Rx)
        m.visual=trimesh.visual.TextureVisuals(material=mat(n))
        sc.add_geometry(m,node_name=f"{n}_{i}",geom_name=f"{n}_{i}")
    # apoyar en el suelo y centrar en planta
    b=sc.bounds; c=(b[0]+b[1])/2
    sc.apply_translation([-c[0],-b[0][1],-c[2]])
    return sc
if __name__=='__main__':
    d="expositor_tabla_"
    inf=piezas(d+"inferior.glb"); med=piezas(d+"media.glb"); sup=piezas(d+"superior.glb")
    up=np.eye(4); up[2,3]=1.2
    balda_med=[(n,m.copy().apply_transform(up) or m) for n,m in med if n.startswith("Part2")]
    for n,m in med:
        pass
    bm=[]
    for n,m in med:
        if n.startswith("Part2"):
            mm=m.copy(); mm.apply_translation([0,0,1.2]); bm.append(("balda_media",mm))
    modulo=[(n,m) for n,m in inf]+bm+[("balda_superior",m) for n,m in sup if n.startswith("Part2")]
    escena(modulo).export("/home/claude/martintorices.github.io/public/modelos/mies.glb")
    # pentágono: cada módulo trae solo la balda media; añadimos la inferior y la superior
    pen=dict(piezas("expositor_todopentagono.glb"))
    bases=sorted([k for k in pen if k.startswith("base")])
    ref=pen["base.1_4"]  # módulo con la misma colocación que el STEP de la balda media
    binf=[m for n,m in inf if n.startswith("Part2")][0].copy(); binf.apply_translation([0,0,-1.2])
    bsup=[m for n,m in sup if n.startswith("Part2")][0].copy(); bsup.apply_translation([0,0,-1.2])
    lista=list(pen.items())
    for k in bases:
        M,_,cost=trimesh.registration.procrustes(ref.vertices,pen[k].vertices,reflection=False,scale=False,return_cost=True)
        for nombre,b in [("balda_inf",binf),("balda_sup",bsup)]:
            bb=b.copy(); bb.apply_transform(M); lista.append((f"{nombre}_{k}",bb))
        print(k,"error",round(cost,8))
    escena(lista).export("/home/claude/martintorices.github.io/public/modelos/mies-pentagono.glb")
    import os
    for f in ["mies.glb","mies-pentagono.glb"]:
        p="/home/claude/martintorices.github.io/public/modelos/"+f; s=trimesh.load(p); print(f,os.path.getsize(p)//1024,"KB",(s.extents*1000).round().tolist())
