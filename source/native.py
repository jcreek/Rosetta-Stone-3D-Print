"""Package grouped STL parts as native Bambu plates. Run Bambu Studio to slice/export."""
from pathlib import Path
import argparse,json,zipfile,uuid
import xml.etree.ElementTree as ET
import numpy as np
import trimesh

root=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('groups',type=Path)
p.add_argument('output',type=Path)
p.add_argument('--template',type=Path,default=root/'P1S template.3mf')
args=p.parse_args()
ns='http://schemas.openxmlformats.org/package/2006/relationships'
ET.register_namespace('',ns)
with zipfile.ZipFile(args.template) as template:
    native={n:template.read(n) for n in template.namelist()}
cfg=ET.Element('config')
def meta(parent,key,value):
    return ET.SubElement(parent,'metadata',key=key,value=str(value))
rels=ET.Element(f'{{{ns}}}Relationships')
config=json.loads(native['Metadata/project_settings.config'])
if args.groups.stem in ('fit','panels'):
    config.update(enable_prime_tower='0',flush_into_infill='0',flush_into_objects='0',flush_into_support='0')
with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
    main='3D/3dmodel.model'
    top=native[main].decode().split(' <resources>')[0]
    model_header=top.splitlines()[1]
    object_xml=[]; build=[]; plates=[]
    obj_id=0
    for plate_number,group in enumerate(json.loads(args.groups.read_text())):
        plate=ET.Element('plate')
        plates.append(plate)
        for k,v in [('plater_id',plate_number+1),('plater_name',group['label']),('bed_type','Textured PEI Plate'),
                    ('filament_maps','1 1'),('filament_volume_maps','0 0'),('filament_map_mode','Auto For Flush')]:
            meta(plate,k,v)
        for item in group['objects']:
            parts=[]
            for name,filament in item['parts']:
                m=trimesh.load_mesh(root/'models'/(name+'.stl'),process=True)
                assert m.is_watertight
                parts.append((name,m,filament))
            low=np.min([m.bounds[0] for _,m,_ in parts],axis=0)
            high=np.max([m.bounds[1] for _,m,_ in parts],axis=0)
            target_x,target_y=item.get('center',[132,128])
            x=target_x-(low[0]+high[0])/2
            y=target_y-(low[1]+high[1])/2
            assert 18<=x+low[0] and x+high[0]<=249 and 12<=y+low[1] and y+high[1]<=248
            x+=(plate_number%4)*307.2
            y-=(plate_number//4)*307.2
            obj_id+=len(parts)+1
            obj=ET.SubElement(cfg,'object',id=str(obj_id))
            meta(obj,'name',item['label']);meta(obj,'extruder',1)
            ins=ET.SubElement(plate,'model_instance')
            for k,v in [('object_id',obj_id),('instance_id',0),('identify_id',65+len(build))]:meta(ins,k,v)
            comps=[]
            for i,(name,m,filament) in enumerate(parts):
                pid=obj_id-len(parts)+i
                path=f'3D/Objects/object_{pid}.model'
                verts='\n'.join(f'<vertex x="{a:.8g}" y="{b:.8g}" z="{c:.8g}"/>' for a,b,c in m.vertices)
                faces='\n'.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in m.faces)
                z.writestr(path,model_header+f'<resources><object id="{pid}" p:UUID="{uuid.uuid4()}" type="model"><mesh><vertices>{verts}</vertices><triangles>{faces}</triangles></mesh></object></resources></model>')
                comps.append(f'<component p:path="/{path}" objectid="{pid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')
                ET.SubElement(rels,f'{{{ns}}}Relationship',Target='/'+path,Id=f'rel-{pid}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
                part=ET.SubElement(obj,'part',id=str(pid),subtype='normal_part',uuid=str(uuid.uuid4()))
                for k,v in [('name',name),('source_file',name+'.stl'),('extruder',filament),('matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')]:
                    meta(part,k,v)
                ET.SubElement(part,'mesh_stat',face_count=str(len(m.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
            object_xml.append(f'<object id="{obj_id}" p:UUID="{uuid.uuid4()}" type="model"><components>{"".join(comps)}</components></object>')
            build.append(f'<item objectid="{obj_id}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 {x} {y} 0" printable="1"/>')
    cfg.extend(plates)
    z.writestr(main,top+'<resources>'+''.join(object_xml)+'</resources><build p:UUID="'+str(uuid.uuid4())+'">'+''.join(build)+'</build></model>')
    z.writestr('3D/_rels/3dmodel.model.rels',ET.tostring(rels))
    z.writestr('Metadata/model_settings.config',ET.tostring(cfg))
    z.writestr('Metadata/project_settings.config',json.dumps(config))
    for name in ['_rels/.rels','[Content_Types].xml']:z.writestr(name,native[name])
