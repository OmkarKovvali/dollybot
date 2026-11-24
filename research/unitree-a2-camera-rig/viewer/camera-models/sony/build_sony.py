"""Sony ZV-E1 visual reference model, not OEM CAD or mounting geometry.
Run with Blender --background --factory-startup --python this_file.
GLB/STL intentionally use viewer-native millimeter coordinates and Z-up.
"""
from pathlib import Path
import bpy, bmesh, math, json, hashlib, struct
from mathutils import Vector, Matrix

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'dist/assets'
PREVIEW=HERE/'previews'
OUT.mkdir(parents=True,exist_ok=True); PREVIEW.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=0.001
MODEL=[]

def material(name,color,metal=0,rough=.5):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    return m
black=material('Sony matte charcoal shell',(.045,.049,.052),.08,.48)
rubber=material('Fine textured black grip',(.016,.019,.022),0,.84)
edge=material('Panel seams and recesses',(.008,.011,.014),0,.7)
control=material('Control black',(.029,.033,.038),.12,.47)
silver=material('Brushed E-mount stainless steel',(.48,.53,.57),.88,.29)
darksilver=material('Shoe and screw dark metal',(.16,.19,.21),.8,.3)
white=material('Warm white printed legends',(.78,.81,.79),0,.6)
red=material('Record red',(.65,.015,.025),.25,.32)
gold=material('Lens contact gold',(.58,.38,.09),.8,.25)
sensor=material('Full-frame sensor cover glass',(.07,.22,.19),.5,.19)
glass=material('Inactive LCD glass',(.013,.029,.043),.3,.16)
# Subtle physical grip bump; the GLB intentionally retains portable base PBR only.
noise=rubber.node_tree.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=135
bump=rubber.node_tree.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.21; bump.inputs['Distance'].default_value=.13
rubber.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']); rubber.node_tree.links.new(bump.outputs['Normal'],rubber.node_tree.nodes.get('Principled BSDF').inputs['Normal'])

def add(o,name,mat):
    o.name=name
    if mat: o.data.materials.append(mat)
    MODEL.append(o); return o

def bevel(o,width,segments=4):
    if width:
        b=o.modifiers.new('Soft molded edge','BEVEL'); b.width=width; b.segments=segments
        b.affect='EDGES'; b.limit_method='ANGLE'
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=b.name)
    for p in o.data.polygons: p.use_smooth=True
    n=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL'); n.keep_sharp=True; n.weight=40
    return o

def box(name,dims,loc,mat=black,r=.5):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=add(bpy.context.object,name,mat); o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); return bevel(o,r)

def cyl(name,radius,depth,loc,mat=control,axis='z',verts=64,edgewidth=.15):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc)
    o=add(bpy.context.object,name,mat)
    if axis=='x': o.rotation_euler[1]=math.pi/2
    elif axis=='y': o.rotation_euler[0]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return bevel(o,edgewidth,3)

def ring(name,ro,ri,depth,loc,mat,axis='x',n=96):
    vs=[]; fs=[]
    for t in [-depth/2,depth/2]:
        for r in [ro,ri]:
            for i in range(n):
                a=i*2*math.pi/n
                if axis=='x': v=(t,r*math.cos(a),r*math.sin(a))
                elif axis=='y': v=(r*math.cos(a),t,r*math.sin(a))
                else: v=(r*math.cos(a),r*math.sin(a),t)
                vs.append(tuple(v[k]+loc[k] for k in range(3)))
    for i in range(n):
        j=(i+1)%n
        fs.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vs,[],fs); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o); add(o,name,mat)
    return bevel(o,.12,2)

def text(name,string,loc,size,mat=white,face='front',align='LEFT'):
    cu=bpy.data.curves.new(name,'FONT'); cu.body=string; cu.align_x=align; cu.size=size; cu.extrude=.015; cu.resolution_u=5
    o=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(o); o.location=loc
    # local text XY axes to camera face; rightward front lettering along +Y.
    if face=='front': rot=Matrix(((0,0,-1),(1,0,0),(0,1,0)))
    elif face=='back': rot=Matrix(((0,0,1),(-1,0,0),(0,1,0)))
    else: rot=Matrix.Identity(3)
    o.rotation_euler=rot.to_euler(); o.data.materials.append(mat)
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.ops.object.convert(target='MESH'); o=bpy.context.object
    MODEL.append(o); return o

def cut(body,tool):
    bpy.context.view_layer.objects.active=body
    m=body.modifiers.new('Lens opening','BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=tool
    bpy.ops.object.modifier_apply(modifier=m.name)
    if tool in MODEL: MODEL.remove(tool)
    bpy.data.objects.remove(tool,do_unlink=True)

def screw(name,loc,axis='x',r=1.35):
    o=cyl(name,r,.35,loc,silver,axis,32,.08)
    a=box(name+' screwdriver slot',(.41,1.6,.12) if axis=='z' else (.12,1.6,.32),loc,edge,.05)
    if axis=='z': a.location.z+=.2
    else: a.location.x-=.21
    return o

# Body and stepped top. Front=-X; grip=-Y; lens axis roughly Y=13,Z=35.
body=box('Main rounded camera chassis',(33,116,65),(4.5,0,33),black,4.0)
cut(body,cyl('Cavity cutter',25.3,28,(-7.0,13,35),None,'x',96,0))
box('Bottom magnesium shell seam',(31.2,112,1.0),(4.7,0,1.0),control,.45)
box('Upper top deck',(32.2,117,5.1),(4.7,0,65.0),black,2.0)
box('Front top fascia',(1.2,110,12),(-12.1,0,60.8),black,.5)
# Ergonomic grip loft: rounded cross-sections and a tapered shoulder.
vs=[]; fs=[]; nseg=10
profile=[]
for cx,cy,start in [(8,-34,0),(-18,-34,90),(-18,-50,180),(8,-50,270)]:
    for i in range(nseg):
        a=math.radians(start+i*90/nseg); profile.append((cx+10*math.cos(a),cy+8*math.sin(a)))
# A robust rounded box profile ordering, counterclockwise around perimeter.
profile=[]
for cx,cy,start in [(8,-34,0),(-18,-34,90),(-18,-50,180),(8,-50,270)]:
    for i in range(nseg):
        a=math.radians(start+i*90/nseg); profile.append((cx+10*math.cos(a),cy+8*math.sin(a)))
for z,s in [(1.5,.88),(4.0,1),(59,1),(65.5,.90)]:
    for x,y in profile: vs.append((-5+(x+5)*s,-42+(y+42)*s,z))
n=len(profile)
fs.append(tuple(range(n-1,-1,-1))); fs.append(tuple(range(3*n,4*n)))
for k in range(3):
    for i in range(n): j=(i+1)%n; fs.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
me=bpy.data.meshes.new('Ergonomic grip'); me.from_pydata(vs,[],fs); me.update()
o=bpy.data.objects.new('Rounded protruding hand grip',me); bpy.context.collection.objects.link(o); add(o,o.name,rubber); bevel(o,.7,3)
box('Grip shoulder control platform',(32,31,5),(-7,-43,64.3),black,3.0)
box('Back thumb rest',(6,19,28),(22.0,-46,48),rubber,3.0)
# Front E-mount, actual hollow ring and recessed sensor.
ring('Black lens mount perimeter',31.1,25.1,4.7,(-13.8,13,35),edge)
ring('Silver E mount flange',29.9,25.2,1.65,(-17.1,13,35),silver)
ring('Inner black E mount wall',25.2,23.7,13,(-8.7,13,35),control)
box('Sensor chamber backing',(.8,45,41),(4.8,13,35),edge,.5)
box('Full-frame sensor border',(.55,37.4,25.6),(4.25,13,35),darksilver,.1)
box('Full-frame image sensor',(.3,35.6,23.8),(3.78,13,35),sensor,.05)
# Thin colored sensor reflection, intentionally no image texture.
box('Sensor coating highlight',(.04,34.8,.30),(3.60,13,46.1),silver,.02)
for i,a in enumerate([48,132,228,312]):
    a=math.radians(a); screw('E-mount flange screw '+str(i+1),(-18.1,13+27.6*math.cos(a),35+27.6*math.sin(a)))
for i in range(10):
    a=math.radians(245+i*4.6); cyl('Lens electronic contact '+str(i+1),.52,.8,(-12.5,13+22*math.cos(a),35+22*math.sin(a)),gold,'x',16,.08)
cyl('White mounting alignment dot',1.1,.3,(-18.2,31.2,56.0),white,'x',32,.06)
# Release button is adjacent to lower grip side of lens mount.
cyl('Lens release button surround',5.3,2.6,(-13.7,-15.0,19.0),edge,'x',48,.4)
cyl('Lens release button',4.1,2.3,(-15,-15,19),control,'x',48,.5)
text('Sony front wordmark','SONY',(-12.82,-23,61),4.2)
text('Alpha camera mark','α',(-12.85,45,59),7.0)
text('E mount face label','E-mount',(-18.11,4.8,59.2),1.65)
cyl('Front recording indicator',1.25,.45,(-12.9,51,65.7),white,'x',32,.1)
# Top microphone grille and hot shoe (shoe is on the screen-hinge side).
box('Microphone recessed surround',(20.8,34.8,1.0),(3,7,67.4),edge,1.0)
box('Microphone grille',(19.8,33.8,.4),(3,7,67.85),darksilver,.7)
for row in range(9):
    for col in range(16):
        cyl('Microphone perforation',.40,.10,(-5.5+row*2.1,-7.7+col*1.95,68.1),edge,'z',8,0)
box('Multi Interface Shoe base',(22.8,19.2,1.4),(4,42.8,68.0),edge,.6)
box('Shoe contact bed',(18,14.2,.45),(4,42.8,68.85),control,.2)
for yy in [34.5,51.1]: box('Shoe steel side rail',(20.5,2,1.5),(4,yy,69.0),silver,.3)
box('Shoe front stop',(2,18.3,1.3),(-6,42.8,69.1),silver,.25)
for yy in range(6): box('Shoe electrical contact',(.7,.65,.15),(-3.2,39.6+yy*1.3,69.2),gold,.05)
# Top controls around grip, with conspicuous red movie button.
cyl('Shutter zoom outer dial',7.1,2.8,(-14.7,-45.5,68.0),control,'z',72,.3)
ring('Shutter metallic trim',5.6,4.7,.55,(-14.7,-45.5,69.7),silver,'z',64)
cyl('Shutter button',4.6,1.0,(-14.7,-45.5,69.7),black,'z',64,.4)
box('Zoom lever tab',(4.0,3.3,1.4),(-18.7,-51.8,68.0),control,.5)
cyl('Movie button surround',6,1.0,(3.2,-33,68.3),control,'z',64,.2)
cyl('Movie button red ring',4.9,.55,(3.2,-33,69.0),red,'z',64,.1)
cyl('Movie button center',3.7,.6,(3.2,-33,69.4),control,'z',64,.2)
box('Still movie S Q selector',(4.4,13.0,1.0),(11,-19.2,68),control,1)
box('Selector raised tab',(3.1,5.2,1.1),(11,-19.2,68.8),silver,.5)
cyl('C1 top button',2.8,.85,(-9,-32.2,67.9),control,'z',48,.2)
text('C1 legend','C1',(-9.9,-29.1,68.0),1.7,face='top')
# Rear control dial at top grip corner, knurled perimeter.
cyl('Rear command dial',7.8,4.8,(16.1,-42.5,66.2),control,'z',72,.35)
for i in range(36):
    a=2*math.pi*i/36
    cyl('Command dial knurl',.35,3,(16.1+7.5*math.cos(a),-42.5+7.5*math.sin(a),66.3),edge,'z',8,0)
# Articulating LCD closed, with visible hinge, bezel and a physically separate panel.
box('Rear display pocket',(1.7,83.5,54),(21.25,13.0,32.9),edge,1.2)
screen_panel=box('Articulating LCD housing closed',(4.9,80.8,51.5),(23.85,13.5,33.0),black,1.7)
box('LCD black bezel',(.35,77,48),(26.45,13.5,33.0),edge,.8)
box('LCD glass inactive',(.15,68.8,39.8),(26.73,14.2,34.1),glass,.35)
text('LCD Sony wordmark','SONY',(26.89,19.0,11.9),2.1,face='back')
for z in [15.1,49.3]: cyl('LCD articulation hinge',3.6,16.2,(22,56.8,z),control,'z',48,.5)
# Rear buttons and multi-direction control wheel.
for name,y,z in [('MENU',-29.8,58.4),('C2',-32.5,49.4),('Fn',-32.5,40.5),('Playback',-32.5,10.6),('Delete',-44.2,10.6)]:
    cyl(name+' rear button surround',3.35,1.15,(23.6,y,z),edge,'x',48,.2)
    cyl(name+' rear button',2.7,1.55,(24.0,y,z),control,'x',48,.25)
    text(name+' white label',{'Playback':'▶','Delete':'C3'}.get(name,name),(25.0,y+2.2,z-.7),1.7,face='back')
ring('Rear four-way control wheel',8.6,4.5,1.8,(24.0,-38.8,25.9),control,'x',72)
cyl('Rear select button',4.1,2,(24.2,-38.8,25.9),control,'x',64,.4)
for a in range(0,360,30):
    a=math.radians(a); cyl('Rear wheel grip notch',.40,1.85,(24.1,-38.8+7.8*math.cos(a),25.9+7.8*math.sin(a)),edge,'x',8,0)
# Side terminal doors with seams, SD latch and hinge bars.
for name,z,h in [('Microphone USB-C door',54,17),('Memory card door',32,25),('HDMI headphone door',11,14)]:
    box(name+' seam',(24.5,1.0,h+1.0),(3.6,58.1,z),edge,1.0)
    box(name,(23.6,1.1,h),(3.6,58.65,z),control,.8)
box('Card access latch',(4.6,1.5,10.5),(4.2,59.3,31),rubber,.7)
# Shoulder strap lugs, discrete metal loops at both ends.
for yy in [-59.3,59.3]:
    ring('Shoulder strap lug',3.35,1.9,1.2,(1.8,yy,62.6),silver,'z',40)
    box('Strap lug foot',(7.4,2.0,2.1),(2,yy*.98,62.2),control,.6)
# Bottom battery door and approximate tripod fitting.
box('Battery compartment closed seam',(36.6,29.5,.55),(-4,-39.6,.65),edge,3.0)
box('Battery compartment door',(34.4,27.3,.65),(-4,-39.6,.55),control,2.6)
box('Battery release latch',(8,4.5,.85),(3.2,-42.3,.4),silver,.5)
ring('Tripod socket visual rim PROVISIONAL',5.6,3.1,.5,(7,13,.35),silver,'z',64)
cyl('Tripod socket dark opening PROVISIONAL',3.05,.08,(7,13,.05),edge,'z',48,0)
for x,y in [(15,-16),(-6,45),(15,45)]: screw('Bottom case screw',(x,y,.6),'z',1.15)

# Apply normals, then fit visual envelope to the three published overall dimensions.
for o in MODEL:
    bpy.context.view_layer.objects.active=o
    for mod in list(o.modifiers):
        try: bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception: pass
bpy.context.view_layer.update()
coords=[o.matrix_world@v.co for o in MODEL for v in o.data.vertices]
lo=Vector([min(p[k] for p in coords) for k in range(3)]); hi=Vector([max(p[k] for p in coords) for k in range(3)])
size=hi-lo; scale=Vector((54.3/size.x,121.0/size.y,71.9/size.z))
# Nominal socket location is only an assembly datum; no dimensional source establishes its XY.
datum=Vector((7,13,lo.z))
for o in MODEL:
    transform=o.matrix_world.copy()
    for v in o.data.vertices:
        p=transform@v.co; v.co=Vector(((p.x-datum.x)*scale.x,-(p.y-datum.y)*scale.y,(p.z-datum.z)*scale.z))
    o.matrix_world=Matrix.Identity(4)
    # Reflect Y to match the real camera handedness, and restore outward winding.
    bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm,faces=list(bm.faces)); bm.to_mesh(o.data); bm.free(); o.data.update()
root=bpy.data.objects.new('Sony_ZV_E1_visual_reference_mm_Zup',None); bpy.context.collection.objects.link(root)
root['units']='millimeters'; root['up_axis']='Z'; root['lens_direction']='-X'; root['fidelity']='photo and manual reconstructed visual reference; not manufacturer CAD'
root['tripod_datum']='XY inferred, unverified; bottom seating plane Z=0'; root['lens_included']=False
for o in MODEL: o.parent=root
lens_origin=[(-18.0-datum.x)*scale.x,(13-datum.y)*scale.y,(35-datum.z)*scale.z]
coords=[v.co for o in MODEL for v in o.data.vertices]
mins=[min(v[k] for v in coords) for k in range(3)]; maxs=[max(v[k] for v in coords) for k in range(3)]
tri_count=0
for o in MODEL: o.data.calc_loop_triangles(); tri_count+=len(o.data.loop_triangles)
meta={
 'title':'Sony ZV-E1 body visual reference', 'created':'2026-11-23',
 'provenance':'Original procedural reconstruction from official Sony dimensions photograph and help-guide drawings. Not Sony CAD, scan, manufacturing or fit geometry.',
 'published_envelope_mm':{'width':121.0,'height':71.9,'depth':54.3},
 'coordinates':{'units':'millimeters','up_axis':'Z','lens_faces':'-X','width_axis':'Y','grip_side':'+Y','origin':'provisional tripod XY and nominal bottom seating plane Z=0','gltf_note':'Intentional viewer-native mm/Z-up GLB. Do not apply usual meter-to-mm or Y-up rotation. STL uses same coordinates.'},
 'bounds_mm':{'min':mins,'max':maxs},'lens_axis':{'face_origin_mm':lens_origin,'direction':[-1,0,0],'location_status':'estimated from references'},
 'tripod_socket':{'nominal_center_mm':[0,0,0],'thread':'1/4-20 UNC','sony_max_entering_screw_length_mm':'strictly less than 5.5','position_status':'UNVERIFIED — not for drilling or fastener placement'},
 'screen':{'state':'closed','articulation':'separate LCD mesh and visible hinge; not rigged or swept-clearance validated','source_range_degrees':{'open':176,'rotate':270}},
 'lens':{'included':False,'reason':'Identified Sony SELP1635G is modeled as separate sony-selp1635g.glb asset','identified_model':'SELP1635G'},
 'features':['rounded chassis','protruding grip','hollow E-mount and recessed full-frame sensor','mount contacts and screws','closed articulated LCD','rear controls and wheel','top microphone perforations','multi-interface shoe','record button and zoom/shutter control','strap lugs','port doors','battery door'],
 'limitations':['Only overall envelope constrained to published dimensions; feature coordinates are visual estimates.','Tripod XY, screen sweep, interface geometry and clearances require measurement.','No structural, print, tolerance or dynamic payload validation.','No lens, cage, windscreen or removable accessory included.'],
 'sources':[{'url':'https://sony.scene7.com/is/image/sonyglobalsolutions/01_Dimensions?fmt=png-alpha&wid=1400','local':'references/official-dimensions.png','use':'front and side photograph; dimensions'},{'url':'https://helpguide.sony.net/ilc/2310/v1/en/print.pdf','local':'../../../printer-cameras/assets/sony-zv-e1-help-guide.pdf','pages':[36,37,39,41,43],'use':'control placement, articulation, bottom and socket notes'},{'url':'https://www.sony-asia.com/interchangeable-lens-cameras/products/zv-e1','use':'published W/H/D'}],
 'mesh':{'objects':len(MODEL),'triangles':tri_count},'exports':['sony-zv-e1.glb','sony-zv-e1.stl'],'viewer_loading':{'scale':[1,1,1],'rotation_radians':[0,0,0]}
}
# Export only model, no scene/lighting. Keep named component meshes and materials.
bpy.ops.object.select_all(action='DESELECT'); root.select_set(True)
for o in MODEL:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/'sony-zv-e1.glb'),export_format='GLB',use_selection=True,export_yup=False,export_extras=True,export_apply=True,export_cameras=False,export_lights=False,export_materials='EXPORT')
# Deterministic binary STL fallback in mm, without losing axis convention.
with open(OUT/'sony-zv-e1.stl','wb') as f:
    f.write(b'Sony ZV-E1 visual reference | mm Zup | tripod XY unverified'.ljust(80,b' '));f.write(struct.pack('<I',tri_count))
    for o in MODEL:
        for tri in o.data.loop_triangles:
            a,b,c=[o.matrix_world@o.data.vertices[i].co for i in tri.vertices]; n=(b-a).cross(c-a).normalized()
            f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
for filename in meta['exports']:
    p=OUT/filename;meta.setdefault('files',{})[filename]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(OUT/'sony-zv-e1.json').write_text(json.dumps(meta,indent=2)+'\n');(HERE/'model-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
# Studio QA renders, separate from exported model.
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.color=(.11,.11,.11)
scene.view_settings.view_transform='AgX'
backdrop=material('Studio background',(.19,.22,.25),0,.85)
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-.8));floor=bpy.context.object;floor.name='QA ground only';floor.data.materials.append(backdrop)
def area(name,loc,power,size,target=(0,-10,35)):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox',(-150,-170,240),450000,180)
area('Fill softbox',(-50,170,160),300000,140)
area('Rear rim',(180,10,190),400000,160)
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=176;cam.data.clip_start=.1;cam.data.clip_end=3000
for label,loc,target in [('front-three-quarter',(-230,205,155),(-8,12.5,35)),('rear-three-quarter',(230,-160,145),(-8,12.5,35)),('front',(-280,12.5,37),(-8,12.5,36)),('top',(-5,12.5,300),(-5,12.5,36))]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    if label=='top':cam.rotation_euler=(0,0,math.pi/2);cam.data.ortho_scale=156
    scene.render.filepath=str(PREVIEW/(label+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'sony-zv-e1.blend'))
print('SONY_MODEL_DONE '+json.dumps(meta['mesh']),flush=True)
