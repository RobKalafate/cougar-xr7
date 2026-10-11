import numpy as np, os
from PIL import Image, ImageFilter
SRC=r'C:\Users\rhkal\AppData\Local\Temp\claude\C--Users-rhkal\c50d7345-d0a9-4127-98ac-6b742ef4643e\images'
OUT=r'C:\Users\rhkal\cougar-xr7\img'
# src, slug, preset
J=[('11.jpg','front-dusk','dusk'),('1.jpg','profile','day'),('2.jpg','night-quarter','night'),
('4.jpg','rear-lamps','night'),('5.jpg','front-rain','night'),('15.jpg','rain-quarter','night'),
('3.jpg','engine-bay','night'),('7.jpg','cockpit-road','day'),('23.png','interior','golden'),
('6.jpg','underside','detail'),('9.jpg','street-wide','dusk'),('17.png','grass-front','golden'),
('16.png','grass-rear','golden'),('19.png','grass-low','golden'),('20.png','grass-hood','golden'),
('21.png','grass-rear-side','golden'),('22.png','grass-overhead','golden')]
P={ # wb strength, gamma, contrast, vibrance, clarity, vignette, hi-clip pct
'day':dict(wb=.30,g=1.0,k=.16,v=.06,c=.10,vig=.10),
'dusk':dict(wb=.30,g=.98,k=.16,v=.04,c=.10,vig=.12),
'night':dict(wb=.55,g=.97,k=.18,v=.0,c=.08,vig=.16),
'golden':dict(wb=.45,g=1.0,k=.14,v=-.05,c=.06,vig=.10),
'detail':dict(wb=.50,g=.98,k=.16,v=.0,c=.12,vig=.08)}
def lum(a): return a[...,0]*.2126+a[...,1]*.7152+a[...,2]*.0722
def grade(im,p):
    a=np.asarray(im,np.float32)/255
    l=lum(a); lo,hi=np.percentile(l,.4),np.percentile(l,99.6)
    a=np.clip((a-lo)/(hi-lo+1e-6),0,1)
    l=lum(a); m=(l>.12)&(l<.85)
    if m.sum()>1000:
        mean=a[m].mean(0); g=mean.mean()/mean
        g=np.clip(g,.8,1.25)**p['wb']; a=np.clip(a*g,0,1)
    a=a**p['g']
    s=a*a*(3-2*a); a=a*(1-p['k'])+s*p['k']
    l=lum(a)[...,None]; sat=(a.max(-1)-a.min(-1))[...,None]
    a=np.clip(l+(a-l)*(1+p['v']*(1-sat)*2),0,1)
    img=Image.fromarray((a*255).astype(np.uint8))
    r=max(img.size)*.012
    bl=np.asarray(img.filter(ImageFilter.GaussianBlur(r)),np.float32)/255
    a=np.clip(a+p['c']*(a-bl)*.9,0,1)
    h,w=a.shape[:2]; y,x=np.ogrid[:h,:w]
    d=((x-w/2)/(w/2))**2+((y-h/2)/(h/2))**2
    a=a*(1-p['vig']*np.clip(d/2,0,1)**1.2)[...,None]
    return Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
if __name__=='__main__':
    for f,slug,pre in J:
        im=Image.open(os.path.join(SRC,f)).convert('RGB')
        if im.height>im.width: target=(1280,int(1280*im.height/im.width))
        else:
            tw=2200 if im.width>2500 else 1600
            target=(tw,int(tw*im.height/im.width))
        im=im.resize(target,Image.LANCZOS)
        g=grade(im,P[pre]).filter(ImageFilter.UnsharpMask(1.0,45,3))
        g.save(os.path.join(OUT,slug+'.jpg'),quality=84,optimize=True,progressive=True)
        t=g.copy(); t.thumbnail((900,900)); t.save(os.path.join(OUT,slug+'-sm.jpg'),quality=80,optimize=True,progressive=True)
        print(slug,g.size)
    
