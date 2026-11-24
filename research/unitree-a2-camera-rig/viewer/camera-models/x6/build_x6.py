"""Photo/manual based Insta360 X6 visual model. Not OEM CAD or fit geometry."""
from pathlib import Path
import bpy, bmesh, math, json, hashlib, struct
from mathutils import Vector, Matrix

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'dist/assets'
PREVIEW=HERE/'previews'
OUT.mkdir(parents=True,exist_ok=True);PREVIEW.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001
MODEL=[]

def mat(name,color,metal=0,rough=.5,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m
shell=mat('Graphite molded body',(.055,.059,.063),.12,.65)
rubber=mat('Textured rubber side panels',(.029,.032,.036),0,.82)
seam=mat('Recess and panel seams',(.009,.012,.015),0,.66)
rim=mat('Replaceable lens bezel',(.035,.040,.046),.45,.28)
trim=mat('Lens machined edge',(.12,.14,.17),.8,.25)
glass=mat('OLED dark glass',(.006,.018,.031),.3,.16)
blue=mat('Illustrative screen blue',(.025,.10,.16),.15,.3)
white=mat('Printed silver legends',(.73,.78,.80),.1,.5)
red=mat('Shutter ring red',(.56,.012,.025),.2,.33)
cyan=mat('Status indicator cyan',(.015,.64,.82),.1,.27,.4)
metal=mat('Mount socket brushed metal',(.23,.26,.29),.85,.28)
gold=mat('Bottom connector pins',(.45,.32,.13),.8,.28)
optics=[mat('Optical coating '+str(i),c,.5,.09) for i,c in enumerate([(.008,.019,.019),(.014,.045,.044),(.025,.061,.075),(.048,.053,.089),(.10,.09,.16)])]
noise=shell.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=175
bump=shell.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=.12
shell.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);shell.node_tree.links.new(bump.outputs['Normal'],shell.node_tree.nodes.get('Principled BSDF').inputs['Normal'])

def add(o,name,material):
    o.name=name
    if material:o.data.materials.append(material)
    MODEL.append(o);return o

def finish(o,r=.2,segments=3):
    if r:
        b=o.modifiers.new('Molded edge radius','BEVEL');b.width=r;b.segments=segments;b.limit_method='ANGLE'
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
    for p in o.data.polygons:p.use_smooth=True
    n=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');n.keep_sharp=True
    return o

def box(name,dims,loc,material=seam,r=.3):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=add(bpy.context.object,name,material);o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,r)

def cyl(name,r,depth,loc,material=seam,axis='x',n=64,bevel=.08):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=loc);o=add(bpy.context.object,name,material)
    if axis=='x':o.rotation_euler[1]=math.pi/2
    elif axis=='y':o.rotation_euler[0]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,bevel)

def ring(name,ro,ri,depth,loc,material,axis='x',n=96):
    vs=[];fs=[]
    for t in (-depth/2,depth/2):
        for r in (ro,ri):
            for j in range(n):
                a=2*math.pi*j/n
                p=(t,r*math.cos(a),r*math.sin(a)) if axis=='x' else (r*math.cos(a),r*math.sin(a),t)
                vs.append(tuple(p[i]+loc[i] for i in range(3)))
    for j in range(n):
        k=(j+1)%n;fs.extend([(j,k,n+k,n+j),(2*n+j,3*n+j,3*n+k,2*n+k),(j,2*n+j,2*n+k,k),(n+j,n+k,3*n+k,3*n+j)])
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(add(o,name,material),.06,2)

def rounded_panel(name,width,height,depth,center,material,corner=4,axis='x'):
    profile=[]
    for cy,cz,a0 in [(width/2-corner,height/2-corner,0),(-width/2+corner,height/2-corner,90),(-width/2+corner,-height/2+corner,180),(width/2-corner,-height/2+corner,270)]:
        for j in range(12):
            a=math.radians(a0+j*90/12);profile.append((cy+corner*math.cos(a),cz+corner*math.sin(a)))
    vs=[]
    for t in (-depth/2,depth/2):
        for y,z in profile:
            p=(t,y,z) if axis=='x' else (y,t,z)
            vs.append(tuple(p[i]+center[i] for i in range(3)))
    n=len(profile);fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    for i in range(n):j=(i+1)%n;fs.append((i,j,n+j,n+i))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(add(o,name,material),min(.18,depth*.2),2)

def text(name,string,loc,size,material=white,side=-1,vertical=False):
    cu=bpy.data.curves.new(name,'FONT');cu.body=string;cu.size=size;cu.extrude=.01;cu.resolution_u=4
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=loc
    rot=Matrix(((0,0,-1),(1,0,0),(0,1,0))) if side==-1 else Matrix(((0,0,1),(-1,0,0),(0,1,0)))
    if vertical:rot=rot@Matrix.Rotation(-math.pi/2,3,'Z')
    o.rotation_euler=rot.to_euler();o.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');MODEL.append(bpy.context.object)

def grille(name,x,y,z,w,h,axis='x',spacing=1.0):
    # Small dark mesh disks retain visible perforation detail in portable GLB.
    for i in range(int(w/spacing)):
        for j in range(int(h/spacing)):
            u=(i-(int(w/spacing)-1)/2)*spacing;v=(j-(int(h/spacing)-1)/2)*spacing
            if abs(u)/(w/2)+abs(v)/(h/2)>1.48:continue
            loc=(x,y+u,z+v) if axis=='x' else (x+u,y,z+v)
            cyl(name+' perforation',.19,.035,loc,seam,axis,8,0)

# Published lens-free envelope is50 W x100 H x26.4 D millimetres.
rounded_panel('Main rounded graphite body',50,100,26.4,(0,0,50),shell,8.4)
rounded_panel('Front molded perimeter seam',48.4,98.4,.30,(-13.14,0,50),seam,8)
rounded_panel('Front textured fascia',47.8,97.8,.34,(-13.32,0,50),shell,7.7)
rounded_panel('Rear molded perimeter seam',48.4,98.4,.30,(13.14,0,50),seam,8)
rounded_panel('Rear textured fascia',47.8,97.8,.34,(13.32,0,50),shell,7.7)

def lens(side):
    label='Front' if side<0 else 'Rear'
    cyl(label+' lens recessed gasket',18.25,.85,(side*13.55,0,78.5),seam)
    ring(label+' replaceable outer lens bezel',17.85,15.2,2.0,(side*14.45,0,78.5),rim)
    ring(label+' fine optical rim',15.55,14.95,.48,(side*15.7,0,78.5),trim)
    for i in range(16):
        a=2*math.pi*i/16;yc=17.20*math.cos(a);zc=78.5+17.20*math.sin(a)
        o=box(label+' lens retaining scallop',(.36,1.5,.65),(side*15.51,yc,zc),seam,.18);o.rotation_euler[0]=a
    # Convex ellipsoidal optical cap: edge at13.8 and apex20 mm.
    n=96;nr=24;vs=[];fs=[]
    for k in range(nr+1):
        theta=(.0001+(math.pi/2-.0001)*k/nr);r=15.0*math.sin(theta);xx=side*(13.8+6.2*math.cos(theta))
        for j in range(n):a=j*2*math.pi/n;vs.append((xx,r*math.cos(a),78.5+r*math.sin(a)))
    for k in range(nr):
        for j in range(n):
            q=(j+1)%n;face=(k*n+j,k*n+q,(k+1)*n+q,(k+1)*n+j);fs.append(face if side<0 else tuple(reversed(face)))
    me=bpy.data.meshes.new(label+' convex fisheye glass');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(label+' convex fisheye glass',me);bpy.context.collection.objects.link(o);add(o,o.name,None)
    for m in optics:o.data.materials.append(m)
    for p in me.polygons:
        row=p.index//n;p.material_index=min(4,int(row/6));p.use_smooth=True
    for rr in (4.8,8.0,11.6,14.1):
        xx=side*(13.8+6.2*math.sqrt(1-(rr/15)**2)+.025)
        ring(label+' concentric optical coating',rr+.07,rr-.07,.035,(xx,0,78.5),optics[2])
    cyl(label+' central entrance pupil',2.0,.035,(side*19.94,0,78.5),optics[0],bevel=0)
    ring(label+' lens alignment groove',17.9,17.55,.18,(side*15.56,0,78.5),seam)
lens(-1);lens(1)

# Front: actual X6 uses screen controls, not the older two-button front layout.
rounded_panel('Front OLED black bezel',43,50.8,.45,(-13.58,0,29.7),seam,5.2)
rounded_panel('Front OLED glass',38.6,46.4,.11,(-13.86,0,29.8),glass,4.1)
rounded_panel('Illustrative dark screen preview',36.8,36.7,.025,(-13.925,0,33.2),blue,3.1)
rounded_panel('Illustrative screen virtual-control strip',36.8,7.3,.025,(-13.95,0,10.9),rim,2.4)
box('Screen virtual button divider',(.03,.16,6.0),(-13.98,0,10.8),white,.02)
cyl('Virtual record circle white',2.03,.04,(-13.99,-9.2,10.9),white,n=48,bevel=0)
cyl('Virtual record circle red',1.70,.045,(-14.025,-9.2,10.9),red,n=48,bevel=0)
rounded_panel('Virtual video icon',3.1,2.8,.04,(-14.02,8.7,11.0),white,.35)
box('Virtual video icon lens',(.04,1.2,1.9),(-14.03,10.6,11),white,.1)
text('Screen illustrative format','8K  50',(-13.99,-5.8,17.3),2.25)
text('Screen illustrative recording time','SD  2h18m',(-13.99,-16.3,49.4),1.45)
rounded_panel('Screen battery icon',3.1,1.7,.03,(-14,15.2,50.1),white,.25)
box('Screen battery icon terminal',(.03,.3,.8),(-14.02,17,50.1),white,.05)
rounded_panel('Front wind microphone surround',6.1,4.7,.24,(-13.6,-16,58.8),rubber,1.8)
grille('Front wind microphone',-13.75,-16,58.8,4.1,3.1,spacing=.65)
rounded_panel('Front ambient light sensor',6.1,4.7,.25,(-13.6,16,58.8),rim,1.8)
rounded_panel('Front cyan status LED',8.5,1.0,.22,(-13.59,0,1.8),cyan,.45)

# Rear microphone cluster, ambient sensor, vertical branding and quick button.
rounded_panel('Rear wind microphone polygon surround',22,12,.34,(13.6,0,51.9),rubber,4.6)
grille('Rear wind microphone',13.81,0,53.3,17,6.5,spacing=.85)
rounded_panel('Rear ambient light sensor',6.7,2.4,.20,(13.82,0,48.1),rim,1.0)
text('Rear vertical Insta360 X6 branding','Insta360 X6',(13.75,1.6,42.1),3.1,side=1,vertical=True)
rounded_panel('Rear quick button gasket',11.2,5.5,.55,(13.56,0,12.2),seam,2.1)
rounded_panel('Rear quick button',9.8,4.4,.65,(13.98,0,12.3),rim,1.8)
for yy in (-2,0,2):box('Rear quick button tactile notch',(.035,.5,.7),(14.34,yy,11.6),rubber,.1)
rounded_panel('Rear cyan status LED',6.6,1.35,.22,(13.5,0,5.2),cyan,.6)

# Right side: wind microphone, power and red-ring shutter, USB access door.
rounded_panel('Right wind microphone surround',8.2,11,.40,(0,24.74,84),rubber,3,axis='y')
grille('Right wind microphone',0,24.98,85.2,5,5,axis='y',spacing=.8)
rounded_panel('Right microphone drainage opening',5.5,1.6,.12,(0,24.99,78.8),seam,.7,axis='y')
rounded_panel('Power shutter side control recess',13.6,30.7,.48,(0,24.65,50),seam,4,axis='y')
rounded_panel('Power button',8.2,8.2,.62,(0,24.94,59.2),rim,2.3,axis='y')
# Power symbol is a thin three-quarter arc with a central stroke.
for j in range(27):
    a=math.radians(45+j*270/26);cyl('Power symbol stroke',.18,.05,(2.2*math.sin(a),25.27,59.2+2.2*math.cos(a)),white,'y',8,0)
box('Power symbol vertical stem',(.32,.04,2.6),(0,25.27,61.0),white,.08)
cyl('Side shutter black surround',5.6,.54,(0,24.84,43.5),rim,'y',64,.18)
cyl('Side shutter red ring',4.65,.18,(0,25.16,43.5),red,'y',64,.06)
cyl('Side shutter center',4.12,.23,(0,25.27,43.5),rubber,'y',64,.14)
rounded_panel('USB cover seam',16.5,18.1,.3,(0,24.73,10.9),seam,1.4,axis='y')
rounded_panel('USB cover face',15.6,17.2,.35,(0,24.95,10.9),rubber,1.3,axis='y')
rounded_panel('USB latch',6.4,4.8,.45,(0,25.23,14),rim,1.2,axis='y')
box('USB latch indicator',(2.0,.04,.45),(0,25.48,15.0),white,.08)

# Opposite side: microphone, six speaker ports and long sealed battery door.
rounded_panel('Left wind microphone surround',8.2,10.5,.45,(0,-24.75,85),rubber,3,axis='y')
grille('Left wind microphone',0,-25.02,85.8,5.1,4.5,axis='y',spacing=.8)
rounded_panel('Left microphone drainage opening',5.5,1.6,.14,(0,-25.04,79.9),seam,.7,axis='y')
for x in (-.9,.9):
    for z in (69.6,71.6,73.6):cyl('Side speaker opening',.55,.10,(x,-24.99,z),seam,'y',16,0)
rounded_panel('Battery door seam',18.6,58.7,.30,(0,-24.7,32),seam,1.6,axis='y')
rounded_panel('Battery door panel',17.9,58,.36,(0,-24.95,32),rubber,1.5,axis='y')
rounded_panel('Battery door locking latch',7.6,7.1,.75,(0,-25.12,25),rim,1.6,axis='y')
box('Battery latch release mark',(2.3,.045,.55),(0,-25.52,27),white,.12)

# Bottom interface details are visual estimates, not a mounting template.
box('Bottom connector mounting panel',(17.5,33.0,.55),(0,0,.38),rim,3.0)
ring('Bottom quarter-inch mounting socket visual rim',4.0,3.05,.35,(0,0,.18),metal,'z',64)
cyl('Bottom socket dark opening',3.02,.05,(0,0,.025),seam,'z',64,0)
for x in (-5.2,5.2):
    for y in (-2.9,2.9):cyl('Bottom magnetic contact',.75,.10,(x,y,.05),gold,'z',24,.02)
for y in (-11.2,11.2):
    for x in (-4.4,4.4):box('Bottom quick release recess',(3.2,3.5,.12),(x,y,.08),seam,.5)
    box('Bottom quick release engagement slot',(1.25,3.8,.12),(0,y,.08),seam,.5)

# Apply modifier normals and constrain only the published global envelope.
for o in MODEL:
    bpy.context.view_layer.objects.active=o
    for modifier in list(o.modifiers):
        try:bpy.ops.object.modifier_apply(modifier=modifier.name)
        except Exception:pass
bpy.context.view_layer.update()
coords=[o.matrix_world@v.co for o in MODEL for v in o.data.vertices]
lo=Vector([min(p[k] for p in coords) for k in range(3)]);hi=Vector([max(p[k] for p in coords) for k in range(3)])
scale=Vector((40/(hi.x-lo.x),50/(hi.y-lo.y),100/(hi.z-lo.z)))
datum=Vector(((hi.x+lo.x)/2,(hi.y+lo.y)/2,lo.z))
for o in MODEL:
    transform=o.matrix_world.copy()
    for v in o.data.vertices:
        p=transform@v.co-datum;v.co=Vector((p.x*scale.x,-p.y*scale.y,p.z*scale.z))
    o.matrix_world=Matrix.Identity(4)
    # Match front-view handedness to the OEM exterior diagrams and restore
    # outward winding after reflecting Y. This also makes lettering readable.
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
root=bpy.data.objects.new('Insta360_X6_visual_reference_mm_Zup',None);bpy.context.collection.objects.link(root)
root['units']='millimeters';root['up_axis']='Z';root['lens_axes']='plus and minus X';root['fidelity']='OEM-photo/manual reconstruction; not manufacturer CAD';root['bottom_datum']='nominal bottom center; mounting socket coordinates unverified'
for o in MODEL:o.parent=root
coords=[v.co for o in MODEL for v in o.data.vertices]
mins=[min(v[k] for v in coords) for k in range(3)];maxs=[max(v[k] for v in coords) for k in range(3)]
triangles=0
for o in MODEL:o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in MODEL:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/'insta360-x6.glb'),export_format='GLB',use_selection=True,export_yup=False,export_extras=True,export_apply=True,export_cameras=False,export_lights=False)
with (OUT/'insta360-x6.stl').open('wb') as f:
    f.write(b'Insta360 X6 visual reference | mm Zup | bottom mounting XY unverified'.ljust(80,b' '));f.write(struct.pack('<I',triangles))
    for o in MODEL:
        for t in o.data.loop_triangles:
            a,b,c=[o.matrix_world@o.data.vertices[i].co for i in t.vertices];n=(b-a).cross(c-a).normalized();f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
meta={'title':'Insta360 X6 detailed visual reference','provenance':'Original procedural reconstruction from official Insta360 product photos and five exterior manual views; not manufacturer CAD, scan or fabrication geometry.','published_dimensions_mm':{'width':50,'height':100,'depth_including_lenses':40,'body_depth_excluding_lenses':26.4},'published_mass_g':196,'coordinates':{'units':'millimeters','up_axis':'Z','lens_axes':['-X','+X'],'screen_faces':'-X','width_axis':'Y','origin':'nominal bottom center Z=0; exact mounting socket position unverified','viewer_loading':{'scale':[1,1,1],'rotation_radians':[0,0,0]},'gltf_note':'Intentional viewer-native mm and Z-up, no meter conversion or Y-up rotation.'},'bounds_mm':{'min':mins,'max':maxs},'mesh':{'objects':len(MODEL),'triangles':triangles},'features':['rounded graphite body','opposed convex fisheye optics with replaceable retaining rings','front OLED and illustrative virtual buttons','front/rear ambient light sensors','four microphone grilles','rear quick button and vertical wordmark','right power/shutter controls and USB door','left battery door and speaker','bottom quarter-inch socket, magnetic contacts and quick-release recesses'],'limits':['Only the published overall envelope is dimensionally constrained; feature locations, lens diameter, body radii, seams and doors are inferred from photos.','Bottom interface is a visual cue; do not derive mounting holes or thread depth from this model.','Display graphics are an illustrative simple UI, not an exact screen capture.','No stick, lens guards, cage or removable accessory included.','Procedural fine body texture is visible in Blender QA; GLB retains portable base PBR materials and explicit grille geometry.'],'sources':[{'url':'https://www.insta360.com/specs/x6','use':'overall dimensions and mass'},{'url':'https://onlinemanual.insta360.com/x6/en-us/specs/hardware','use':'26.4 mm body depth excluding lenses'},{'url':'https://onlinemanual.insta360.com/x6/en-us/camera/product-introduction/insta360-x6','use':'five official exterior diagrams and part identification','local':'references/manual-*.jpeg'},{'url':'https://www.insta360.com/product/insta360-x6','use':'front/rear surface appearance','local':'references/official-hero.jpg'}],'files':{}}
for name in ('insta360-x6.glb','insta360-x6.stl'):
    p=OUT/name;meta['files'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(OUT/'insta360-x6.json').write_text(json.dumps(meta,indent=2));(HERE/'model-metadata.json').write_text(json.dumps(meta,indent=2))
print('X6_ASSET_READY '+json.dumps(meta['mesh']),flush=True)

# Separate studio QA scene; lights and cameras are not exported to GLB.
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED';scene.render.threads=8;scene.world.color=(.13,.13,.13)
scene.view_settings.view_transform='AgX'
floor_mat=mat('QA studio floor',(.13,.16,.19),0,.8)
bpy.ops.mesh.primitive_plane_add(size=1500,location=(0,0,-.5));floor=bpy.context.object;floor.data.materials.append(floor_mat)
def light(loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,50))-o.location).to_track_quat('-Z','Y').to_euler();return o
light((-180,-130,210),360000,150);light((-60,180,150),260000,130);light((180,40,190),420000,150)
bottom_light=light((-70,60,-150),240000,130);bottom_light.hide_render=True
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=140;cam.data.clip_start=.1;cam.data.clip_end=2000
for name,loc,target in [('front-three-quarter',(-210,135,130),(0,0,49)),('rear-three-quarter',(210,-130,130),(0,0,49)),('bottom',(-130,110,-150),(0,0,35))]:
    floor.hide_render=(name=='bottom');bottom_light.hide_render=(name!='bottom')
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PREVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'insta360-x6.blend'))
print('X6_MODEL_DONE',flush=True)
