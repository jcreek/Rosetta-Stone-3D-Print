"""Make bow-tie fit samples with actual engraving cut from the production seam."""
import json
from pathlib import Path
import trimesh
from shapely import wkt, make_valid
from shapely.affinity import translate
from shapely.geometry import Polygon, box

root=Path(__file__).resolve().parent
repo=root.parents[1]
data=json.loads((repo/'docs'/'Assembly data.json').read_text())
seam=data['width_mm']/3
pocket=min((b for b in data['pockets'] if abs((b[0]+b[2])/2-seam)<1e-5 and b[2]-b[0]>20),
           key=lambda b:abs((b[1]+b[3])/2-540))
cy=(pocket[1]+pocket[3])/2
row=4-int(cy//225)
key=Polygon(data['key_outline_mm'])
top,floor,white_base,pocket_depth,key_depth=5.12,3.56,3.32,1.56,1.44
assert abs(floor-pocket_depth-2)<1e-8 and abs(top-floor-1.56)<1e-8

def polygons(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    return [p for x in g.geoms for p in polygons(x)]

def extrude(shape,z0,z1):
    units=[]
    for p in polygons(make_valid(shape)):
        if p.area<1e-7:continue
        m=trimesh.creation.extrude_polygon(p,z1-z0,engine='earcut')
        m.apply_translation([0,0,z0])
        units.append(m)
    return trimesh.util.concatenate(units)

def save(mesh,name):
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,name
    mesh.export(root/'models'/(name+'.stl'))

save(extrude(translate(key,-key.bounds[0],-key.bounds[1]),0,key_depth),'Deep key')
jobs=[];checks={}
for tag,clearance,y in [('A',.10,145),('B',.16,102)]:
    pocket=key.buffer(clearance,quad_segs=8)
    assert pocket.covers(key) and abs(key.distance(pocket.boundary)-clearance)<.003
    def free(gap):
        left=translate(pocket.intersection(box(-20,-10,0,10)),-gap/2,0)
        right=translate(pocket.intersection(box(0,-10,20,10)),gap/2,0)
        return left.union(right).union(box(-gap/2,-10,gap/2,10))
    lo,hi=0,3
    for _ in range(25):
        gap=(lo+hi)/2
        if free(gap).covers(key):lo=gap
        else:hi=gap
    checks[tag]={'nominal_clearance_per_side_mm':clearance,'nominal_xy_seam_play_mm':round(lo,3)}
    for i,col in enumerate((1,2)):
        panel=f'R{row} C{col}'
        info=next(p for p in data['panels'] if p['label']==panel)
        ox,oy=info['offset_mm']
        x0,x1=(seam-21,seam) if not i else (seam,seam+21)
        y0=cy-9
        footprint=box(0,0,21,18)
        grooves=wkt.loads((repo/'source'/'Engraving profiles'/(panel+'.wkt')).read_text())
        grooves=make_valid(translate(grooves,ox-x0,oy-y0).intersection(footprint))
        cavity=make_valid(translate(pocket,seam-x0,cy-y0).intersection(footprint))
        body=extrude(footprint,0,top)
        if not grooves.is_empty:
            body=trimesh.boolean.difference([body,extrude(grooves,floor,top+.12)],engine='manifold')
        white=extrude(footprint,white_base,floor)
        for cutter in (white,extrude(cavity,-.12,pocket_depth)):
            body=trimesh.boolean.difference([body,cutter],engine='manifold')
        name=f'{tag} - '+('left half' if not i else 'right half')
        save(body,name+' black')
        save(white,name+' white')
        jobs.append({'label':name,'parts':[[name+' black',1],[name+' white',2]],'center':[84+43*i,y]})
    jobs.append({'label':tag+' - Deep key','parts':[['Deep key',1]],'center':[169,y]})
(root/'fit.json').write_text(json.dumps([{'label':'A rear 0.10 mm - B front 0.16 mm','objects':jobs}]))
(root/'Joint checks.json').write_text(json.dumps({'panel_thickness_mm':top,'floor_height_mm':floor,'pocket_depth_mm':pocket_depth,'key_thickness_mm':key_depth,'sample_seam':f'R{row} C1 / C2','variants':checks},indent=2))
