import sys,os
from PIL import Image,ImageDraw
SRC=r'C:\Users\rhkal\AppData\Local\Temp\claude\C--Users-rhkal\c50d7345-d0a9-4127-98ac-6b742ef4643e\images'
OUT=r'C:\Users\rhkal\AppData\Local\Temp\claude\C--Users-rhkal\c50d7345-d0a9-4127-98ac-6b742ef4643e\scratchpad'
for f in sys.argv[1:]:
    im=Image.open(os.path.join(SRC,f)).convert('RGB')
    s=1000/im.width; im=im.resize((1000,round(im.height*s)))
    d=ImageDraw.Draw(im)
    for x in range(0,1000,50):
        c=(255,255,0) if x%100==0 else (255,255,255)
        d.line([(x,0),(x,im.height)],fill=c+(0,),width=1)
        if x%100==0: d.text((x+2,2),str(x),fill=(255,255,0))
    for y in range(0,im.height,50):
        c=(255,255,0) if y%100==0 else (255,255,255)
        d.line([(0,y),(1000,y)],fill=c,width=1)
        if y%100==0: d.text((2,y+2),str(y),fill=(255,255,0))
    im.save(os.path.join(OUT,'g_'+f.split('.')[0]+'.png'))
    print(f,im.size)
