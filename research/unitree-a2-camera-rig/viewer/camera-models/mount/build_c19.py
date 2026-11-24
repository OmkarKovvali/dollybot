"""INNOREL C19 visual reference from manufacturer photos; not OEM/fabrication CAD."""
from pathlib import Path
import bpy, bmesh, math, json, hashlib, struct
from mathutils import Vector, Matrix

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'dist/assets'; PREVIEW=HERE/'previews'
OUT.mkdir(parents=True,exist_ok=True); PREVIEW.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=.001
MODEL=[]

def mat(name,color,metal=0,rough=.5):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    return m
black=mat('Black anodized CNC aluminum',(.041,.047,.055),.76,.32)
knurl=mat('Machined knurl satin edges',(.051,.057,.065),.8,.36)
steel=mat('Black steel stud and ball',(.025,.030,.038),.82,.23)
rubber=mat('Camera pad textured rubber',(.028,.031,.035),0,.78)
dark=mat('Grooves and socket interior',(.009,.012,.017),.25,.48)
silver=mat('Stainless thread reducer adapter',(.42,.46,.49),.92,.24)
white=mat('INNOREL printed model legends',(.76,.79,.81),.2,.46)

def add(o,name,material):
    o.name=name
    if material:o.data.materials.append(material)
    MODEL.append(o); return o
def mesh(name,vs,fs,material,smooth=True):
    me=bpy.data.meshes.new(name); me.from_pydata(vs,[],fs); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); add(o,name,material)
    for p in me.polygons:p.use_smooth=smooth
    return o
def finish(o,r=.1,segments=2):
    if r:
        b=o.modifiers.new('Small machined edge bevel','BEVEL'); b.width=r; b.segments=segments
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=b.name)
    for p in o.data.polygons:p.use_smooth=True
    n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); n.keep_sharp=True
    return o
def cyl(name,r,h,loc,material=black,axis='z',n=96,bevel=.1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=h,location=loc)
    o=add(bpy.context.object,name,material)
    if axis=='y':o.rotation_euler[0]=math.pi/2
    elif axis=='x':o.rotation_euler[1]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,bevel)
def box(name,dims,loc,material=black,r=.1):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=add(bpy.context.object,name,material);o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,r)
def lathe(name,profile,material=black,n=144,axis='z',center=(0,0,0),teeth=0,twist=0,depth=.3):
    # Closed section profile with outward normals repaired below. Tooth tips retain profile radius.
    vs=[];fs=[]
    for r,z in profile:
        for j in range(n):
            a=2*math.pi*j/n; rr=r
            if teeth:rr-=depth*(.5-.5*math.cos(teeth*a+twist*z))
            p=(rr*math.cos(a),rr*math.sin(a),z)
            if axis=='y':p=(p[0],-p[2],p[1])
            vs.append(tuple(p[k]+center[k] for k in range(3)))
    for i in range(len(profile)):
        q=(i+1)%len(profile)
        for j in range(n):k=(j+1)%n;fs.append((i*n+j,i*n+k,q*n+k,q*n+j))
    o=mesh(name,vs,fs,material,not bool(teeth))
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    return o
def ring(name,ro,ri,z0,z1,material=black,n=96):
    return lathe(name,[(ri,z0),(ro,z0),(ro,z1),(ri,z1)],material,n)
def subtract(o,cutter):
    bpy.context.view_layer.objects.active=o
    m=o.modifiers.new('Actual open aperture','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
    bpy.ops.object.modifier_apply(modifier=m.name)
    MODEL.remove(cutter);bpy.data.objects.remove(cutter,do_unlink=True)
def label(name,string,loc,size,rot):
    cu=bpy.data.curves.new(name,'FONT');cu.body=string;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.006;cu.resolution_u=3
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=rot;o.data.materials.append(white)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');MODEL.append(bpy.context.object)

# Nominal Ø30 bottom plate. Bottom central hole remains open for the supplied reducer.
lathe('Fine knurled rotary bottom plate',[(4.8,0),(14.75,0),(15,.3),(15,2.25),(14.75,2.5),(4.8,2.5)],knurl,240,teeth=120,depth=.24)
ring('Bottom plate upper hairline seam',14.72,4.75,2.48,2.72,dark)
lathe('Diagonal knurled main clamp barrel',[(4.75,2.7),(14.8,2.7),(15,3.2),(15,6.2),(15,9.2),(15,12.2),(15,14.9),(14.75,15.4),(4.75,15.4)],knurl,288,teeth=96,twist=-.75,depth=.48)
ring('Upper barrel shoulder',14.4,9.7,15.1,16.2,black)

# Hollow upper clamp cup and both opposing U-slots; slot radii are photo estimates.
cup=lathe('Upper ball retaining cup with double U notches',[(9.65,15.7),(14.2,15.7),(14.25,16.5),(14.25,18.0),(13.82,18.45),(13.82,18.85),(14.25,19.25),(14.25,24.2),(13.82,24.65),(13.82,25.1),(14.25,25.5),(14.25,28.25),(13.9,28.8),(9.65,28.8)],black,160)
slot=box('U-slot rectangular cutter',(40,9.2,16),(0,0,30),r=0);subtract(cup,slot)
slot=cyl('U-slot rounded bottom cutter',4.6,40,(0,0,22),axis='x',n=80,bevel=0);subtract(cup,slot)
finish(cup,.14,2)
bpy.ops.mesh.primitive_uv_sphere_add(segments=80,ring_count=40,radius=9.5,location=(0,0,25.05))
ball=add(bpy.context.object,'Published Ø19 polished ball',steel)
for p in ball.data.polygons:p.use_smooth=True
lathe('Ball-to-platform neck',[(0,31),(4.75,31),(4.55,32.6),(4.55,37.8),(5.0,38.0),(0,38.0)],steel,96)

# Top platform sits below the rubber contact plane42.5; published total47.5 includes stud.
lathe('Fine knurled camera platform',[(0,37.8),(14.0,37.8),(14.4,38.15),(14.4,41.35),(14.0,41.7),(0,41.7)],knurl,288,teeth=144,depth=.28)
ring('Rubber top pad foundation',11.9,2.7,41.7,42.36,rubber,144)
for ix in range(-8,9):
    for iy in range(-8,9):
        x=ix*1.35;y=iy*1.35
        if math.hypot(x,y)>10.9 or math.hypot(x,y)<3.5:continue
        box('Rubber pad crosshatch cell',(1.15,1.15,.14),(x,y,42.43),rubber,.06)

# Actual visible helical form is an approximate visual thread, not a machinable helix.
cyl('Quarter inch screw root',2.59,5.0,(0,0,45),steel,n=96,bevel=.12)
turns=3.75;steps=240;vs=[];fs=[]
for i in range(steps+1):
    a=i/steps*2*math.pi*turns; z=42.55+i/steps*4.65
    for r,dz in [(2.56,-.32),(3.175,0),(2.56,.32)]:vs.append((r*math.cos(a),r*math.sin(a),min(47.5,max(42.5,z+dz))))
for i in range(steps):
    for j in range(3):k=(j+1)%3;fs.append((3*i+j,3*(i+1)+j,3*(i+1)+k,3*i+k))
mesh('Top 1/4-20 visual screw thread',vs,fs,steel)

# The locking control faces -Y to be reachable to the side of the Sony.
cyl('Main locking knob spindle',3.6,9.0,(0,-16.5,14.5),steel,'y',64,.15)
lathe('Main knob rear shoulder',[(0,16.7),(8.4,16.7),(9.0,17.3),(9.1,18.1),(0,18.1)],black,96,'y',(0,0,14.5))
lathe('Diagonal knurled main locking knob',[(0,18),(8.9,18),(9.35,18.5),(9.35,21.5),(9.35,24.5),(9.35,27.5),(9.35,30),(8.95,30.6),(0,30.6)],knurl,192,'y',(0,0,14.5),teeth=64,twist=-.9,depth=.38)
cyl('Main knob machined endcap',8.85,.45,(0,-30.65,14.5),black,'y',96,.15)
cyl('Main knob endcap circular inset',8.0,.12,(0,-30.91,14.5),black,'y',96,.05)
# Small recessed retention set screw seen on the barrel opposite the main control.
cyl('Small barrel set-screw recess',1.22,.16,(0,14.88,11.1),dark,'y',40,.03)
cyl('Small barrel set screw',.88,.10,(0,14.98,11.1),steel,'y',6,.02)

# Adapter is shown installed in the C19 base. Seating/flange depth is not published.
ring('Installed 3/8 to 1/4 reducer adapter',4.67,3.18,.04,4.4,silver,96)
for z in (.5,1.77,3.04):ring('Bottom adapter inner thread visual groove',3.3,2.72,z,z+.35,silver,72)
ring('Bottom recessed socket mouth',5.2,4.68,.01,.23,dark)
# Flat screwdriver slots visible from below; visual recesses do not determine fit.
for x in (-3.9,3.9):box('Adapter screwdriver slot',(1.25,.55,.04),(x,0,.025),dark,.02)
label('Bottom model mark','C19',(0,-9,.012),2.0,(math.pi,0,0))
label('Bottom brand legend','INNOREL',(0,8,.012),2.4,(math.pi,0,0))

# Apply all geometry and use viewer-native raw millimetres/Z-up without export rotations.
for o in MODEL:
    bpy.context.view_layer.objects.active=o
    for m in list(o.modifiers):
        try:bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception:pass
    transform=o.matrix_world.copy()
    for v in o.data.vertices:v.co=transform@v.co
    o.matrix_world=Matrix.Identity(4)
root=bpy.data.objects.new('INNOREL_C19_upright_visual_reference_mm_Zup',None);bpy.context.collection.objects.link(root)
root['units']='millimeters';root['up_axis']='Z';root['camera_seating_plane_z_mm']=42.5;root['seating_height_status']='photo-inferred provisional';root['commercial_part']='INNOREL C19, Amazon ASIN B0CHB63882';root['fidelity']='Manufacturer-photo reconstruction, not OEM CAD or printable clone'
for o in MODEL:o.parent=root
bpy.context.view_layer.update()
coords=[v.co for o in MODEL for v in o.data.vertices]
lo=[min(v[k] for v in coords) for k in range(3)];hi=[max(v[k] for v in coords) for k in range(3)]
tri=0
for o in MODEL:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in MODEL:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/'innorel-c19.glb'),export_format='GLB',use_selection=True,export_yup=False,export_extras=True,export_apply=True,export_cameras=False,export_lights=False)
meta={'title':'INNOREL C19 low-profile mini ball head','amazon_asin':'B0CHB63882','model_role':'Detailed commercial mount visual reference; not manufacturer CAD, measured model or printable replacement.','camera_seating_plane_z_mm':42.5,'camera_seating_plane_height_status':'Provisional image-derived estimate; no independent OEM dimension found. Includes rubber pad, excludes stud.','total_height_including_stud_mm':47.5,'published_dimensions_mm':{'overall_height_including_stud':47.5,'base_diameter':30,'ball_diameter':19},'published_mass_g':59,'interfaces':{'camera_top':'1/4-inch male screw (modeled as conventional1/4-20)','native_bottom':'3/8-inch female hole','installed_adapter':'Supplied 3/8 to1/4-inch reducer, modeled installed flush','bottom_axis_origin_mm':[0,0,0],'camera_axis_xy_mm':[0,0],'estimated_exposed_stud_mm':5,'thread_engagement_depth_mm':None,'adapter_flange_depth_status':'Unverified; depicted flush for visual assembly'},'coordinates':{'units':'millimeters','up_axis':'Z','origin':'Bottom center on ball axis, nominal flat base Z0','knob_direction':'-Y','pose':'Ball upright, top platform level, no pan/tilt articulation animation','viewer_loading':{'scale':[1,1,1],'rotation_radians':[0,0,0]}},'bounds_mm':{'min':lo,'max':hi},'mesh':{'objects':len(MODEL),'vertices':len(coords),'triangles':tri},'limits':['Only Ø30 base, Ø19 ball, total47.5 mm stud-tip height and59g are manufacturer-published dimensional/mass anchors.','Camera seating42.5 mm and5 mm exposed stud, platform/knob diameter, housing profiles, thread details, adapter seating and slot locations are inferred from photos.','Bottom thread and camera screw lengths must be physically checked; do not derive engagement depths from this visual mesh.','Rated3kg static marketing payload is not a robot dynamic-load qualification.','The lower base cannot be treated as a certified47.5 mm camera spacer:47.5 reaches the stud tip.'],'sources':[{'url':'https://innoreltech.com/products/cnc-metal-low-profile-mini-ballhead-innorel-c19','use':'Primary manufacturer product identity, mass, material, double U slots and threaded interfaces','local':'references/official-product.html'},{'url':'https://innoreltech.com/cdn/shop/files/INNOREL-tripod-head-C19-specifications.jpg?v=1773826806&width=3840','use':'Primary graphic shows height arrow from bottom to stud tip; Ø19 ball and Ø30 base','local':'references/official-dimensions.jpg'},{'url':'https://innoreltech.com/cdn/shop/files/INNOREL_C19_product_details.jpg?v=1773827645&width=3840','use':'Rubber pad, double U slots, main knob, bottom3/8 hole and3/8→1/4 reducer','local':'references/official-details.jpg'},{'url':'https://www.amazon.com/dp/B0CHB63882','use':'User-selected purchase reference, no purchase performed'}],'files':{}}
p=OUT/'innorel-c19.glb';raw=p.read_bytes();json_length=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+json_length])
meta['mesh']['glb_position_vertices']=sum(gltf['accessors'][primitive['attributes']['POSITION']]['count'] for mesh in gltf['meshes'] for primitive in mesh['primitives'])
meta['files'][p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(OUT/'innorel-c19.json').write_text(json.dumps(meta,indent=2));(HERE/'model-metadata.json').write_text(json.dumps(meta,indent=2))
print('C19_ASSET_READY '+json.dumps(meta['mesh']),flush=True)

# Product-view QA. Lights/cameras never enter the GLB.
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED';scene.render.threads=8;scene.world.color=(.14,.14,.14);scene.view_settings.view_transform='AgX'
floor_mat=mat('QA neutral floor',(.12,.145,.17),0,.8)
bpy.ops.mesh.primitive_plane_add(size=800,location=(0,0,-.3));floor=bpy.context.object;floor.data.materials.append(floor_mat)
def light(loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,24))-o.location).to_track_quat('-Z','Y').to_euler();return o
light((-100,-90,140),95000,95);light((100,-35,95),75000,75);light((10,100,120),110000,85)
bottomlight=light((-40,-50,-90),75000,75);bottomlight.hide_render=True
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=77;cam.data.clip_start=.1;cam.data.clip_end=1000
for name,loc,target in [('three-quarter',(95,-145,90),(0,-5,23)),('opposite',(110,145,70),(0,-4,23)),('bottom',(80,-100,-115),(0,-4,18))]:
    floor.hide_render=(name=='bottom');bottomlight.hide_render=(name!='bottom');cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PREVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'innorel-c19.blend'))
print('C19_MODEL_DONE',flush=True)
