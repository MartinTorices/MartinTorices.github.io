"""Texturas procedurales (sin fotos de terceros) para los modelos 3D de MIES.

Genera en public/modelos/texturas/:
  chopo-cara-*.jpg   chapa de chopo desenrollado: veta suave y vetas grisáceas
  chopo-canto-*.jpg  canto del contrachapado de 25 mm: chapas cruzadas y líneas de cola
  aluminio-*.jpg     aluminio gris antracita cepillado a lo largo del perfil
  cuerda-*.jpg       cuerda de yute de tres cabos
  estudio.hdr        iluminación de estudio (cajas de luz) para model-viewer

Cada material lleva: -color (sRGB), -orm (R oclusión, G rugosidad, B metal) y -normal.
Uso: python3 herramientas/mies_texturas.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.join(os.path.dirname(__file__), '..', 'public', 'modelos', 'texturas')
os.makedirs(RAIZ, exist_ok=True)
rng = np.random.default_rng(7)


def ruido(h, w, sy, sx):
    """Ruido periódico (se repite sin costuras). sy, sx: tamaño del grano en píxeles."""
    blanco = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    filtro = np.exp(-((fy * sy) ** 2 + (fx * sx) ** 2))
    r = np.real(np.fft.ifft2(np.fft.fft2(blanco) * filtro))
    return (r - r.mean()) / (r.std() + 1e-9)


def mezcla(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.array(a) * (1 - t) + np.array(b) * t


def normal_desde_altura(h, fuerza):
    dy, dx = np.gradient(h)
    # vecinos con vuelta (textura periódica)
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    n = np.dstack([-dx * fuerza, dy * fuerza, np.ones_like(h)])  # +Y arriba (convenio glTF)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def guardar(nombre, arr, calidad=88):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(
        os.path.join(RAIZ, nombre), quality=calidad, optimize=True, progressive=True)


def orm(rug, metal, ao=None):
    ao = np.ones_like(rug) if ao is None else ao
    return np.dstack([ao * 255, np.clip(rug, 0, 1) * 255, np.full_like(rug, metal * 255)])


# ── Chopo, cara (1 m × 1 m, veta a lo largo de u) ───────────────────────────
N = 2048
# ruido(alto, ancho, sy, sx): sy y sx son el tamaño de las manchas en píxeles
lento = ruido(N, N, 260, 700)         # ondulación grande de la veta
medio = ruido(N, N, 60, 260)          # ondulación pequeña
fibra = ruido(N, N, 1.5, 160)         # fibras finas, alargadas a lo largo de la veta
mancha = ruido(N, N, 220, 420)        # nubes de color amplias
gris = ruido(N, N, 22, 320)           # vetas minerales grisáceas, típicas del chopo
v = np.linspace(0, 1, N, endpoint=False)[:, None]
fase = v * 11 + lento * 1.05 + medio * 0.15
anillo = 0.5 + 0.5 * np.sin(2 * np.pi * fase)
anillo = anillo ** 4                  # líneas finas y oscuras de la veta, separadas
t = 0.45 * anillo + 0.12 * (fibra * 0.5 + 0.5) + 0.3 * (mancha * 0.5 + 0.5)
color = mezcla((232, 210, 172), (203, 174, 128), t)
vg = np.clip((gris - 1.6) * 0.8, 0, 1)
color = mezcla(color, (176, 166, 144), vg * 0.3)
guardar('chopo-cara-color.jpg', color, 86)
altura = anillo * 0.5 + fibra * 0.15
peq = lambda a: np.array(Image.fromarray(a).resize((1024, 1024), Image.LANCZOS))
guardar('chopo-cara-normal.jpg', peq(normal_desde_altura(altura, 1.2)), 90)
rug = 0.6 + 0.06 * anillo + 0.03 * fibra
guardar('chopo-cara-orm.jpg', peq(orm(rug, 0).astype(np.uint8)), 90)

# ── Chopo, canto (u: 0,5 m que se repite; v: los 25 mm del tablero) ─────────
W, H = 2048, 256
capas = 11
bordes = np.cumsum(np.r_[0, 1 + rng.uniform(-0.12, 0.12, capas)])
bordes = bordes / bordes[-1]
vv = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
idx = np.clip(np.searchsorted(bordes, vv, side='right') - 1, 0, capas - 1)
fib = ruido(H, W, 1.5, 40)
poros = ruido(H, W, 1.2, 1.2)
largo = idx % 2 == 0                   # chapas con la veta a lo largo
c_largo = mezcla((226, 205, 168), (205, 180, 138), 0.5 + 0.25 * fib)
c_testa = mezcla((206, 182, 140), (176, 150, 108), 0.5 + 0.35 * poros)
color = np.where(largo[..., None], c_largo, c_testa)
# líneas de cola entre chapas
dist = np.min(np.abs(vv[..., None] - bordes[None, None, 1:-1]), axis=2)
cola = np.clip(1 - dist / 0.012, 0, 1)
color = mezcla(color, (150, 124, 86), cola * 0.8)
guardar('chopo-canto-color.jpg', color, 88)
altura = np.where(largo, fib * 0.2, poros * 0.5) - cola * 0.8
guardar('chopo-canto-normal.jpg', normal_desde_altura(altura, 2.0), 90)
guardar('chopo-canto-orm.jpg', orm(np.where(largo, 0.66, 0.78) + 0.05 * poros, 0).astype(np.uint8), 90)

# ── Aluminio antracita cepillado (u: 0,2 m; v: 1 m a lo largo del perfil) ───
N = 1024
cep = ruido(N, N, 260, 1.2)            # rayas finas del cepillado (a lo largo de v)
cep2 = ruido(N, N, 90, 4)
nube = ruido(N, N, 14, 14)
base = np.array((112, 115, 121), float)   # gris antracita (aluminio anodizado)   # gris titanio (aluminio anodizado)
color = base[None, None, :] * (1 + 0.015 * cep2[..., None] + 0.015 * nube[..., None])
guardar('aluminio-color.jpg', color, 90)
guardar('aluminio-normal.jpg', normal_desde_altura(cep * 0.5 + cep2 * 0.3, 0.5), 90)
guardar('aluminio-orm.jpg', orm(0.34 + 0.03 * cep + 0.02 * nube, 1).astype(np.uint8), 90)

# ── Cuerda de yute (u: vuelta completa; v: 4 cm de largo) ─────────────────
W, H = 256, 512
u = np.linspace(0, 1, W, endpoint=False)[None, :]
v = np.linspace(0, 1, H, endpoint=False)[:, None]
cabo = 0.5 + 0.5 * np.cos(2 * np.pi * (3 * u + 4 * v))      # tres cabos retorcidos
pelo = ruido(H, W, 2, 12)
altura = cabo ** 0.6 + 0.15 * pelo
color = mezcla((122, 98, 62), (196, 168, 120), altura)
guardar('cuerda-color.jpg', color, 88)
guardar('cuerda-normal.jpg', normal_desde_altura(altura, 3.5), 90)
guardar('cuerda-orm.jpg', orm(0.88 + 0.0 * altura, 0).astype(np.uint8), 90)


# ── Iluminación de estudio en HDR (equirectangular) ─────────────────────────
def guardar_hdr(ruta, img):
    """Radiance .hdr con compresión RLE por canal."""
    h, w, _ = img.shape
    m = img.max(axis=2)
    e = np.ceil(np.log2(np.maximum(m, 1e-32))).astype(int)
    e = np.where(m < 1e-32, -128, e)
    esc = np.where(m < 1e-32, 0, 256.0 / np.exp2(e))
    rgbe = np.zeros((h, w, 4), np.uint8)
    rgbe[..., :3] = np.clip(img * esc[..., None], 0, 255).astype(np.uint8)
    rgbe[..., 3] = np.clip(e + 128, 0, 255) * (m >= 1e-32)
    salida = bytearray(b'#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n')
    salida += f'-Y {h} +X {w}\n'.encode()
    for y in range(h):
        salida += bytes([2, 2, w >> 8, w & 255])
        for c in range(4):
            fila = rgbe[y, :, c]
            i = 0
            while i < w:
                j = i
                while j < w and j - i < 127 and fila[j] == fila[i]:
                    j += 1
                if j - i >= 4:
                    salida += bytes([128 + j - i, int(fila[i])])
                    i = j
                    continue
                k = i
                while k < w and k - i < 128:
                    if k + 3 < w and fila[k] == fila[k + 1] == fila[k + 2] == fila[k + 3]:
                        break
                    k += 1
                salida += bytes([k - i]) + bytes(fila[i:k].tolist())
                i = k
    open(ruta, 'wb').write(salida)


W, H = 1024, 512
az = (np.arange(W) + 0.5) / W * 2 * np.pi - np.pi           # -π..π
el = np.pi / 2 - (np.arange(H) + 0.5) / H * np.pi             # π/2..-π/2
AZ, EL = np.meshgrid(az, el)
# fondo: techo algo más claro que el suelo, como un estudio gris
cielo = np.clip(EL / (np.pi / 2), -1, 1)
img = np.ones((H, W, 3)) * (0.62 + 0.28 * cielo)[..., None]
img *= np.array([1.0, 0.98, 0.95])


def caja(az0, el0, ancho, alto, fuerza, color=(1, 1, 1)):
    """Caja de luz rectangular con bordes suaves (ángulos en grados)."""
    da = (AZ - np.radians(az0) + np.pi) % (2 * np.pi) - np.pi
    de = EL - np.radians(el0)
    sa = np.clip((np.radians(ancho / 2) - np.abs(da) * np.cos(EL)) / 0.02 + 0.5, 0, 1)
    se = np.clip((np.radians(alto / 2) - np.abs(de)) / 0.02 + 0.5, 0, 1)
    return (sa * se)[..., None] * fuerza * np.array(color)


img += caja(-40, 35, 50, 30, 10, (1, 0.97, 0.92))   # principal, delante a la izquierda
img += caja(65, 20, 30, 40, 4.5, (0.92, 0.96, 1))   # relleno, a la derecha
img += caja(170, 40, 70, 12, 5)                     # contra, detrás
img += caja(0, 80, 120, 14, 5)                      # tira cenital
guardar_hdr(os.path.join(RAIZ, '..', 'estudio.hdr'), img.astype(np.float32))

for f in sorted(os.listdir(RAIZ)) + ['../estudio.hdr']:
    print(f, os.path.getsize(os.path.join(RAIZ, f)) // 1024, 'KB')
