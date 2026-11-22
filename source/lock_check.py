"""Check that the bow-tie can be inserted but catches against both pockets."""
from pathlib import Path
import json
from shapely.geometry import Polygon,box
from shapely.affinity import translate
root=Path(__file__).resolve().parent
a=json.loads((root/'Assembly data.json').read_text())
key=Polygon(a['key_outline_mm'])
pocket=Polygon(a['pocket_outline_mm'])
assert pocket.covers(key)
assert abs(key.distance(pocket.boundary)-a['key_clearance_mm'])<.002
left=pocket.intersection(box(-20,-10,0,10))
right=pocket.intersection(box(0,-10,20,10))
def space(gap):
    l=translate(left,-gap/2,0)
    r=translate(right,gap/2,0)
    return l.union(r).union(box(-gap/2,-10,gap/2,10))
lo,hi=0.,6.
for i in range(25):
    mid=(lo+hi)/2
    if space(mid).covers(key):lo=mid
    else:hi=mid
# Both tails catch at a widened section before either key end clears a panel.
assert hi<2 and not space(3).covers(key)
# A generous outward pull exceeds the clearance on each side.
gap=3
assert key.intersection(box(-20,-10,-gap/2,10)).difference(translate(left,-gap/2,0)).area>0
assert key.intersection(box(gap/2,-10,20,10)).difference(translate(right,gap/2,0)).area>0
report={'nominal_clearance_per_side_mm':a['key_clearance_mm'],'key_size_mm':[key.bounds[2]-key.bounds[0],key.bounds[3]-key.bounds[1],a['key_thickness_mm']],
        'max_simulated_centered_seam_opening_mm':round(lo,3),
        'physical_fit_verified':False,'pocket_depth_mm':a['pocket_depth_mm'],'key_count':a['key_count']}
(root/'Lock geometry checks.json').write_text(json.dumps(report,indent=2))
print(report)
