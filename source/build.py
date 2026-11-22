"""Build the 900 mm planar relief and recessed alignment keys from the original grid."""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import gaussian_filter, grey_closing
from shapely import STRtree, make_valid, union_all, wkt
from shapely.geometry import Polygon, box
from shapely.affinity import affine_transform,translate,rotate
from skimage.measure import find_contours
import trimesh
from PIL import Image, ImageDraw

root=Path(__file__).resolve().parent
out=root/'models'
source=root/'Source data'/'reconstruction_grid.npz'
grid=np.load(source)
x,y,z,mask=(grid[k] for k in ('x_mm','y_mm','z_mm','outline_mask'))
step_x,step_y=(x[1]-x[0])*1.5,(y[0]-y[1])*1.5
def polygonal(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    if hasattr(g,'geoms'):return [p for a in g.geoms for p in polygonal(a)]
    return []
def contours(a,level,area_min,simplify,perimeter_min=0):
    rings=[]
    for rc in find_contours(np.pad(a,1),level):
        xy=np.column_stack(((rc[:,1]-1)*step_x,900-(rc[:,0]-1)*step_y))
        for p in polygonal(make_valid(Polygon(xy))):
            if p.area>=area_min and p.length>=perimeter_min:rings.append(p)
    tree=STRtree(rings)
    sizes=np.asarray([p.area for p in rings])
    parents=[-1]*len(rings)
    for i,p in enumerate(rings):
        hits=[j for j in tree.query(p,predicate='within') if sizes[j]>sizes[i]+1e-7]
        if hits:parents[i]=min(hits,key=lambda j:sizes[j])
    children=[[] for _ in rings]
    for i,j in enumerate(parents):
        if j>=0:children[j].append(i)
    depth=[-1]*len(rings)
    def level_of(i):
        if depth[i]<0:depth[i]=0 if parents[i]<0 else 1+level_of(parents[i])
        return depth[i]
    pieces=[Polygon(p.exterior,[rings[j].exterior for j in children[i]]) for i,p in enumerate(rings) if level_of(i)%2==0]
    return make_valid(union_all(pieces).simplify(simplify,preserve_topology=True))

silhouette=contours(mask,.5,20,.10)
xmin,ymin,xmax,ymax=silhouette.bounds
# Snap the outline's traced bounding box to precisely 900 mm in Y.
h_factor=900/(ymax-ymin)
def normalize(shape):return affine_transform(shape,[1,0,0,h_factor,-xmin,-ymin*h_factor])
outline=normalize(silhouette)
width=outline.bounds[2]
# Reuse the already-built panel cut polygons. Geometry changes are limited to the rear pockets.
prior=root/'Engraving profiles'
white_footprint=outline.buffer(-.65,join_style=2)
white_footprint=make_valid(white_footprint)
xs=np.linspace(0,width,4); ys=np.linspace(0,900,5)
# Four millimetres of material are not required at the cuts. Preserve exactly
# 2 mm beneath the floor even over an alignment pocket.
floor,top,white_start,pocket_depth=3.56,5.12,3.32,1.56
pocket_half_length,pocket_half_width=14,4.2
pockets=[]
# Wide tails capture both panels in-plane. A symmetric center neck gives
# each panel a positive mechanical shoulder with the same clearance.
key_shape=Polygon([(-13.7,-3.9),(-4,-3.9),(-3.5,-2.35),(3.5,-2.35),
                   (4,-3.9),(13.7,-3.9),(13.7,3.9),(4,3.9),
                   (3.5,2.35),(-3.5,2.35),(-4,3.9),(-13.7,3.9)])
key_shape=key_shape.buffer(-.55,join_style=2).buffer(.55,quad_segs=6)
pocket_shape=key_shape.buffer(.16,quad_segs=8)
def place(seam,lo,hi,vertical):
    # Pick positions separated along the usable part of the seam, including
    # at tapered edges where one tile is much smaller than its grid cell.
    candidates=[]
    for t in np.linspace(lo+12,hi-12,161):
        sh=translate(pocket_shape,seam,t) if vertical else translate(rotate(pocket_shape,90,origin=(0,0)),t,seam)
        if white_footprint.covers(sh):candidates.append((t,sh))
    if not candidates:return
    indices=[int(.25*(len(candidates)-1)),int(.75*(len(candidates)-1))]
    if candidates[indices[1]][0]-candidates[indices[0]][0]<30:indices=[len(candidates)//2]
    for i in indices:pockets.append(candidates[i][1])
for xcut in xs[1:-1]:
    for a,b in zip(ys[:-1],ys[1:]):place(xcut,a,b,True)
for ycut in ys[1:-1]:
    for a,b in zip(xs[:-1],xs[1:]):place(ycut,a,b,False)
assert len(pockets)>10
def extrude(shape,z0,z1):
    meshes=[]
    for p in polygonal(shape):
        if p.area<1e-7:continue
        m=trimesh.creation.extrude_polygon(p,z1-z0,engine='earcut')
        m.apply_translation((0,0,z0))
        meshes.append(m)
    return trimesh.util.concatenate(meshes)
def save(m,name):
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,name
    m.export(out/(name+'.stl'))
def subtract(m,shape,z0,z1):
    if shape.is_empty:return m
    return trimesh.boolean.difference([m,extrude(shape,z0,z1)],engine='manifold')
preview=Image.new('RGB',(820,1040),'#f6f3ed');draw=ImageDraw.Draw(preview)
factor=1.02
def px(x,y):return (70+x*factor,55+(900-y)*factor)
def color(shape,fill,holes):
    for p in polygonal(shape):
        draw.polygon([px(x,y) for x,y in p.exterior.coords],fill=fill)
        for ring in p.interiors:draw.polygon([px(x,y) for x,y in ring.coords],fill=holes)
color(outline,'#292929','#f6f3ed')
records=[]
for row in range(4):
    for col in range(3):
        a,b=xs[col:col+2]; c,d=ys[3-row:5-row]
        cell=box(a,c,b,d)
        tile=make_valid(outline.intersection(cell))
        label=f'R{row+1} C{col+1}'
        g=translate(wkt.loads((prior/(label+'.wkt')).read_text()),a,c)
        white=make_valid(white_footprint.intersection(cell))
        slots=union_all([s.intersection(cell) for s in pockets if s.intersects(cell)])
        assert g.difference(white).area<1e-7
        # Plane and grooves are defined globally. Only clipping creates the
        # seam, so the open cuts and white stratum line up across both sides.
        black=extrude(tile,0,top)
        for shape,z0,z1 in [(g,floor,top+.10),(white,white_start,floor),(slots,-.10,pocket_depth)]:
            black=subtract(black,shape,z0,z1)
        insert=extrude(white,white_start,floor)
        black.apply_translation((-a,-c,0))
        insert.apply_translation((-a,-c,0))
        label=f'R{row+1} C{col+1}'
        save(black,label+' - Black');save(insert,label+' - White')
        (out/(label+'.wkt')).write_text(translate(g,-a,-c).wkt)
        records.append(dict(label=label,offset_mm=[float(a),float(c)],bounds_mm=black.bounds.tolist(),
                            black_volume_mm3=black.volume,white_volume_mm3=insert.volume,cut_area_mm2=g.area,
                            cut_components=len(polygonal(g))))
        color(g,'#eee9df','#292929')
        print(label,len(black.faces),len(insert.faces),flush=True)
for xc in xs[1:-1]:draw.line([px(xc,0),px(xc,900)],fill='#ca6139',width=2)
for yc in ys[1:-1]:draw.line([px(0,yc),px(width,yc)],fill='#ca6139',width=2)
for r in records:
    a,c=r['offset_mm'];u,v=px(a+16,c+205)
    draw.rectangle((u-4,v-3,u+41,v+14),fill='#f6f3ed')
    draw.text((u,v),r['label'],fill='#a34322')
draw.text((70,18),'Rosetta Stone · 900 mm · assembly from the front',fill='#222222')
draw.text((70,1000),'Dry fit with the face up. Fit the keys into the recessed pockets on the back.',fill='#222222')
preview.save(root/'Assembly diagram.png')
# Separate thin key. The pocket is 28 × 8.4 mm where halves meet.
key=extrude(translate(key_shape,-key_shape.bounds[0],-key_shape.bounds[1]),0,1.44)
save(key,'Alignment key')
# Exact count, slot locations, and volumes are included for independent checks.
(root/'Assembly data.json').write_text(json.dumps(dict(width_mm=width,height_mm=900,
    thickness_mm=top,groove_depth_mm=round(top-floor,2),min_backing_mm=round(floor-pocket_depth,2),
    pocket_depth_mm=pocket_depth,key_thickness_mm=1.44,key_clearance_mm=.16,key_outline_mm=list(key_shape.exterior.coords),pocket_outline_mm=list(pocket_shape.exterior.coords),pockets=[list(p.bounds) for p in pockets],
    key_count=len(pockets),panels=records),indent=2))
