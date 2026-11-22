import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps

data=json.loads(Path('Assembly data.json').read_text())
original=Image.open('Assembly diagram.png').convert('RGB')
s=1.02
w=data['width_mm']
# Mirror the front-view silhouette. Draw the pocket outlines in actual
# reflected XY position; panel labels follow the rear-view order.
image=Image.new('RGB',(820,1040),'#f6f3ed');draw=ImageDraw.Draw(image)
for num,panel in enumerate(data['panels']):
    a,b=panel['offset_mm']
    (lo,hi)=panel['bounds_mm']
    u0=70+(w-a-hi[0])*s;u1=70+(w-a-lo[0])*s
    v0=55+(900-b-hi[1])*s;v1=55+(900-b-lo[1])*s
    draw.rectangle((u0,v0,u1,v1),outline='#968d80',width=2)
    draw.text((u0+8,v0+7),panel['label'],fill='#4d443b')
for i,(a,b,c,d) in enumerate(data['pockets']):
    u0=70+(w-c)*s;u1=70+(w-a)*s
    v0=55+(900-d)*s;v1=55+(900-b)*s
    cx,cy=(a+c)/2,(b+d)/2
    ring=data['pocket_outline_mm']
    if d-b>c-a:ring=[(-y,x) for x,y in ring]
    draw.polygon([(70+(w-cx-x)*s,55+(900-cy-y)*s) for x,y in ring],fill='#623c2a')
draw.text((70,18),'Rear view · joining key positions · rough panel bounding boxes',fill='#222222')
draw.text((70,1000),f"{data['key_count']} recesses span the seams. Place one key in each assembled pocket.",fill='#222222')
image.save('Rear key layout.png')
