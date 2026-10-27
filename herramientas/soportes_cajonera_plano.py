import matplotlib, sys; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
plt.rcParams['font.family']='DejaVu Sans'
EN = len(sys.argv)>1 and sys.argv[1]=='en'
L = (dict(alz='ELEVATION',pla='PLAN',tapa='Caps (×3): head Ø10 × 2, shank Ø4.5 × 8',nerv='ribs t = 2, every 30') if EN else
     dict(alz='ALZADO',pla='PLANTA',tapa='Tapas (×3): cabeza Ø10 × 2, vástago Ø4,5 × 8',nerv='nervios e = 2, cada 30'))
K='#1c1b19'; lw=1.3; lt=0.6
fig,ax=plt.subplots(figsize=(14,6.6)); ax.set_aspect('equal'); ax.axis('off')
def ch(x1,x2,y,txt,yref):
    ax.annotate('',xy=(x1,y),xytext=(x2,y),arrowprops=dict(arrowstyle='<|-|>',color=K,lw=lt,mutation_scale=7,shrinkA=0,shrinkB=0))
    ax.text((x1+x2)/2,y+1.2,txt,ha='center',va='bottom',fontsize=10,color=K)
    for x in (x1,x2): ax.plot([x,x],[yref,y+(1 if y>yref else -1)],color=K,lw=lt*0.8)
def cv(x,y1,y2,txt,xref):
    ax.annotate('',xy=(x,y1),xytext=(x,y2),arrowprops=dict(arrowstyle='<|-|>',color=K,lw=lt,mutation_scale=7,shrinkA=0,shrinkB=0))
    ax.text(x-1.5,(y1+y2)/2,txt,ha='right',va='center',fontsize=10,color=K,rotation=90)
    for y in (y1,y2): ax.plot([xref,x-1],[y,y],color=K,lw=lt*0.8)
eje=dict(color=K,lw=lt*0.7,ls=(0,(10,2,2,2)))
Y=40
ax.add_patch(Rectangle((-118,Y),236,6,fill=False,ec=K,lw=lw))
for xc in (-110,0,110):
    ax.add_patch(Rectangle((xc-4,Y+6),8,12,fill=False,ec=K,lw=lw))
    for d in (-2.5,2.5): ax.plot([xc+d]*2,[Y+6,Y+18],color=K,lw=lt,ls=(0,(4,2)))
    ax.plot([xc,xc],[Y-3,Y+22],**eje)
for xc in (-110,0,110): ax.add_patch(Rectangle((xc-5,Y+18),10,2,fill=False,ec=K,lw=lw))
ax.plot([-113,-100,-60],[Y+20,Y+36,Y+36],color=K,lw=lt)
ax.text(-58,Y+36,L['tapa'],fontsize=9.5,color=K,ha='left',va='center')
cv(-128,Y,Y+18,'18',-118); cv(-122,Y,Y+6,'6',-118)
ch(-110,0,Y+26,'110',Y+18); ch(0,110,Y+26,'110',Y+18)
ax.text(-118,Y+44,L['alz'],fontsize=11,color=K,fontweight='bold')
P=0
ax.add_patch(FancyBboxPatch((-118,P-8),236,16,boxstyle="round,pad=0,rounding_size=8",fill=False,ec=K,lw=lw))
ax.add_patch(FancyBboxPatch((-116,P-6),232,12,boxstyle="round,pad=0,rounding_size=6",fill=False,ec=K,lw=lt))
for xr in (-90,-60,-30,30,60,90):
    ax.add_patch(Rectangle((xr-1,P-6),2,12,fill=True,fc='white',ec=K,lw=lt))
for xc in (-110,0,110):
    ax.add_patch(Circle((xc,P),4,fc='white',ec=K,lw=lw)); ax.add_patch(Circle((xc,P),2.5,fill=False,ec=K,lw=lt))
    ax.plot([xc-7,xc+7],[P,P],**eje); ax.plot([xc,xc],[P-7,P+7],**eje)
ch(-118,118,P-17,'236',P-8)
cv(-128,P-8,P+8,'16',-118)
ax.annotate('Ø8',xy=(2.9,P+2.9),xytext=(12,P+13),fontsize=10,color=K,arrowprops=dict(arrowstyle='-',color=K,lw=lt))
ax.annotate('Ø5',xy=(-1.8,P-1.8),xytext=(-16,P-15),fontsize=10,color=K,arrowprops=dict(arrowstyle='-',color=K,lw=lt))
ax.annotate('R8',xy=(118-2.4,P+5.6),xytext=(123,P+13),fontsize=10,color=K,arrowprops=dict(arrowstyle='-',color=K,lw=lt))
ax.annotate(L['nerv'],xy=(60,P+5),xytext=(38,P+13),fontsize=9.5,color=K,arrowprops=dict(arrowstyle='-',color=K,lw=lt))
ax.text(-118,P+14,L['pla'],fontsize=11,color=K,fontweight='bold')
ax.set_xlim(-140,140); ax.set_ylim(-26,88)
plt.savefig(sys.argv[2] if len(sys.argv)>2 else 'plano.png',dpi=170,bbox_inches='tight',pad_inches=0.15,facecolor='white')
