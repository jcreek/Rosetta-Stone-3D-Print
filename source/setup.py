from pathlib import Path
import json, math
import trimesh
import numpy as np
from shapely.geometry import box
from shapely import wkt

root=Path(__file__).resolve().parent
models=root/'models'
data=json.loads((root/'Assembly data.json').read_text())
panels=data['panels']
def write(name,groups):
    (root/(name+'.json')).write_text(json.dumps(groups,indent=2))
groups=[]
for p in panels:
    label=p['label']
    groups.append({'label':label,'objects':[{'label':label,'parts':[[label+' - Black',1],[label+' - White',2]]}]})
write('panels',groups)
# A sample from an actual shared seam. Preserve both half-pockets and the
# original flat rear faces, including the exact slot clearance.
seam=data['width_mm']/3
pocket=min((b for b in data['pockets']
            if abs((b[0]+b[2])/2-seam)<1e-5 and b[2]-b[0]>20),
           key=lambda b:abs((b[1]+b[3])/2-540))
cy=(pocket[1]+pocket[3])/2
row=4-int(cy//225)
fit=[]
for col,i in [(1,0),(2,1)]:
    src=f'R{row} C{col}';meta=next(p for p in panels if p['label']==src)
    a,b=meta['offset_mm']
    world_left,world_right=(seam-21,seam) if i==0 else (seam,seam+21)
    clip_bbox=[world_left-a,cy-9-b,world_right-a,cy+9-b]
    u,v,w,h=clip_bbox
    components=[]
    for name,filament in [('Black',1),('White',2)]:
        loaded=trimesh.load_mesh(models/f'{src} - {name}.stl',process=True)
        crop=trimesh.creation.box(extents=[w-u,h-v,6],transform=trimesh.transformations.translation_matrix([(u+w)/2,(v+h)/2,2.5]))
        part=trimesh.boolean.intersection([loaded,crop],engine='manifold')
        assert part.is_watertight and part.volume>0
        part.apply_translation([-u,-v,0])
        label=f'Fit {i+1} - {name}'
        part.export(models/(label+'.stl'))
        components.append([label,filament])
    fit.append({'label':f'Fit {i+1} - '+src,'parts':components,'center':[88+55*i,135]})
fit.append({'label':'Alignment key','parts':[['Alignment key',1]],'center':[115,100]})
write('fit',[{'label':'One seam and one alignment key','objects':fit}])
keys=[]
for i in range(data['key_count']+2):
    keys.append({'label':f'Key {i+1:02d}','parts':[['Alignment key',1]],'center':[40+34*(i%6),50+17*(i//6)]})
write('keys',[{'label':'Assembly keys and two spares','objects':keys}])

# Confirm matching incision and slot openings on the shared cuts, for every
# pair that actually touches. XY line intervals are compared in world space.
from shapely.geometry import LineString
from shapely.affinity import translate
maximum=0
relations=[]
for i,p in enumerate(panels):
    a,b=p['offset_mm']
    g=translate(wkt.loads((models/(p['label']+'.wkt')).read_text()),a,b)
    for j,axis in [(i+1,0),(i+3,1)]:
        if j>=len(panels) or (axis==0 and i%3==2):continue
        q=panels[j]; c,d=q['offset_mm']
        other=translate(wkt.loads((models/(q['label']+'.wkt')).read_text()),c,d)
        line=LineString([(c,b),(c,b+225)]) if axis==0 else LineString([(a,b),(a+data['width_mm']/3,b)])
        errors=g.intersection(line).difference(other.buffer(.00002)).length+other.intersection(line).difference(g.buffer(.00002)).length
        maximum=max(maximum,errors)
        relations.append({'pieces':[p['label'],q['label']], 'mismatched_groove_mm':errors})
assert maximum<.0001,maximum
(root/'Seam checks.json').write_text(json.dumps(relations,indent=2))
