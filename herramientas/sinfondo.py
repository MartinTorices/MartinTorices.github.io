# Quita el fondo blanco: el fondo y las sombras grises (conectados con el borde) pasan a
# transparencia; la pieza queda totalmente opaca.
import numpy as np, sys
from PIL import Image
from scipy import ndimage
def sin_fondo(ruta):
    a=np.asarray(Image.open(ruta).convert("RGB")).astype(np.float32)
    mx=a.max(2); mn=a.min(2)
    neutro=((mx-mn)<14)&(mn>140)         # blanco y sombras grises claras
    lab,n=ndimage.label(neutro)
    idx=np.arange(1,n+1)
    tam=ndimage.sum(np.ones_like(lab),lab,index=idx)
    blancos=ndimage.sum(mn>247,lab,index=idx)
    ok=idx[(tam>0.0004*lab.size)&(blancos>0.25*tam)]
    fondo=np.isin(lab,ok)
    # la sombra se oscurece hacia la pieza: crecer el fondo por grises suaves (sin bordes marcados)
    gris=a.mean(2)
    grad=np.hypot(ndimage.sobel(gris,0),ndimage.sobel(gris,1))
    sombra=((mx-mn)<12)&(mn>45)&(grad<40)
    fondo=ndimage.binary_propagation(fondo,mask=fondo|sombra)
    fondo=ndimage.binary_opening(fondo,iterations=1)
    alpha=np.ones(mx.shape,np.float32)
    af=(255-a).max(2)/255.0; af[af<0.02]=0
    alpha[fondo]=af[fondo]
    # suaviza el borde de la pieza
    borde_pieza=ndimage.binary_dilation(~fondo,iterations=1)&fondo
    alpha[borde_pieza]=np.maximum(alpha[borde_pieza],0.5)
    col=a.copy()
    f=fondo&(alpha>0)
    col[f]=np.clip((a[f]-255*(1-alpha[f][:,None]))/alpha[f][:,None],0,255)
    return Image.fromarray(np.dstack([col,alpha*255]).astype(np.uint8),"RGBA")
def encuadrar(img, aspecto=None, centro_pieza=False, margen=0.03):
    A=img.getchannel("A")
    # quita motas sueltas (restos del recorte de la lámina) antes de medir
    m_=np.asarray(A)>8
    lab,n=ndimage.label(ndimage.binary_dilation(m_,iterations=3))
    if n>1:
        tam=ndimage.sum(m_,lab,index=np.arange(1,n+1))
        keep=np.isin(lab,np.arange(1,n+1)[tam>0.002*tam.sum()])
        arr=np.asarray(img).copy(); arr[~keep,3]=0; img=Image.fromarray(arr,"RGBA"); A=img.getchannel("A")
    tot=A.point(lambda v:255 if v>8 else 0).getbbox()
    obj=A.point(lambda v:255 if v>200 else 0).getbbox() if centro_pieza else tot
    cx=(obj[0]+obj[2])/2; cy=(obj[1]+obj[3])/2
    hw=max(cx-tot[0],tot[2]-cx); hh=max(cy-tot[1],tot[3]-cy)
    m=margen*max(hw,hh)*2; hw+=m; hh+=m
    if aspecto:
        if hw/hh<aspecto: hw=hh*aspecto
        else: hh=hw/aspecto
    can=Image.new("RGBA",(int(2*hw),int(2*hh)),(0,0,0,0))
    can.paste(img,(int(hw-cx),int(hh-cy)))
    return can
if __name__=="__main__":
    src,dst=sys.argv[1],sys.argv[2]
    asp=float(sys.argv[3]) if len(sys.argv)>3 and sys.argv[3]!="-" else None
    cp=len(sys.argv)>4
    im=encuadrar(sin_fondo(src),asp,cp)
    im.thumbnail((2000,2000),Image.LANCZOS); im.save(dst,optimize=True); print(dst,im.size)
