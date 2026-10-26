"""Lee el .obj de OVUM G-1 (exportado de Fusion, en cm) separando sus grupos «g»."""
import numpy as np


def leer(ruta):
    V, N, grupos, actual = [], [], {}, None
    with open(ruta, encoding='latin1') as f:
        for l in f:
            if l.startswith('v '):
                V.append(l.split()[1:4])
            elif l.startswith('vn '):
                N.append(l.split()[1:4])
            elif l.startswith('g '):
                actual = l[2:].strip()
                grupos.setdefault(actual, [])
            elif l.startswith('f '):
                c = [p.split('/') for p in l.split()[1:]]
                vi = [int(p[0]) - 1 for p in c]
                ni = [int(p[2]) - 1 if len(p) > 2 and p[2] else -1 for p in c]
                for k in range(1, len(c) - 1):  # abanico por si hay polígonos
                    grupos[actual].append((vi[0], vi[k], vi[k + 1], ni[0], ni[k], ni[k + 1]))
    V = np.array(V, float)
    N = np.array(N, float) if N else None
    piezas = {}
    for g, caras in grupos.items():
        a = np.array(caras, int)
        pares = np.stack([a[:, :3].ravel(), a[:, 3:].ravel()], 1)  # (vértice, normal) por esquina
        uniq, inv = np.unique(pares, axis=0, return_inverse=True)
        pos = V[uniq[:, 0]]
        nor = N[uniq[:, 1]] if N is not None and (uniq[:, 1] >= 0).all() else None
        piezas[g] = (pos, nor, inv.reshape(-1, 3))
    return piezas


if __name__ == '__main__':
    import sys
    for g, (p, n, f) in leer(sys.argv[1]).items():
        print(repr(g), len(p), len(f), p.min(0).round(2), p.max(0).round(2))
