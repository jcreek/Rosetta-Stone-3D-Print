"""Draw the actual bow-tie and pocket outlines from the assembly data."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parent
data=json.loads((root/'Assembly data.json').read_text())
image=Image.new('RGB',(960,410),'#f6f3ed')
d=ImageDraw.Draw(image)
regular='/System/Library/Fonts/Supplemental/Arial.ttf'
f=ImageFont.truetype(regular,21);small=ImageFont.truetype(regular,17)
d.text((40,24),'Bow-tie joint, viewed from the back',font=f,fill='#252525')
d.rectangle((65,120,480,296),fill='#4b4b4b')
d.rectangle((481,120,895,296),fill='#646464')
d.line((480,112,480,306),fill='#eae2d6',width=3)
def xy(coords):return [(480+x*18,208-y*18) for x,y in coords]
d.polygon(xy(data['pocket_outline_mm']),fill='#c4b6a3')
d.polygon(xy(data['key_outline_mm']),fill='#d88442')
for start,end in [(410,315),(550,645)]:
    d.line((start,336,end,336),width=3,fill='#4b3e38')
    direct=1 if end<start else -1
    d.polygon([(end,336),(end+direct*12,329),(end+direct*12,343)],fill='#4b3e38')
d.text((40,373),'The shoulders catch if the panels pull apart. The key drops in from the back.',font=small,fill='#252525')
image.save(root/'How the bow-tie key locks.png')
