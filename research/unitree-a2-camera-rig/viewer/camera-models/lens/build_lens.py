"""Sony FE PZ 16-35mm F4 G visual reference model, not OEM CAD or mounting geometry.
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

# Official envelope: 80.5 mm maximum diameter, 88.1 mm flange-to-front length.
# Profile/feature stations below are visual estimates from the official side photo.
profile=[(0,29.7),(-1.2,30.3),(-2,30.5),(-12,30.5),(-13,31.0),(-21.8,36.5),(-22.8,36.8),(-31.4,36.8),(-32,36.65),(-51.4,36.65),(-53,37.6),(-67.6,37.6),(-69,39.7),(-78.8,39.7),(-80,39.2),(-87.6,39.2),(-88.1,38.7),(-88.1,36.0),(-82.5,35.7),(-81,31.3),(-76,30.8),(-75,0.0),(0,0.0)]

def lathe(name,prof,mat,n=128,teeth=0):
    vs=[];fs=[]
    for x,r in prof:
        for j in range(n):
            a=j*math.tau/n
            ripple=([0,.30,.30,0][j%4] if teeth else 0)
            rr=max(0,r-ripple)
            vs.append((x,rr*math.cos(a),rr*math.sin(a)))
    for i in range(len(prof)-1):
        for j in range(n):
            k=(j+1)%n;fs.append((i*n+j,i*n+k,(i+1)*n+k,(i+1)*n+j))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);add(o,name,mat)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    return o

body=lathe('Tapered fixed internal-zoom barrel',profile,black,192)
# Dedicated ring meshes with modeled fine longitudinal flutes.
def fluted(name,x1,x2,r,mat):
    return lathe(name,[(x1,r-.65),(x1-.55,r),(x2+.55,r),(x2,r-.65),(x2,r-1.0),(x1,r-1.0),(x1,r-.65)],mat,640,True)
fluted('Front focus ring longitudinal ribs',-69.0,-79.0,40.25,rubber)
fluted('Middle power zoom control ring longitudinal ribs',-53.5,-67.3,38.5,rubber)
fluted('Rear aperture ring longitudinal ribs',-27.0,-31.0,37.2,control)
for xx,rr in [(-52.8,37.7),(-68.1,38.0),(-79.6,39.5),(-32.1,36.8)]:
    ring('Narrow ring separation groove',rr,rr-.65,.7,(xx,0,0),edge,'x',128)
# Flange seats at X0. Bayonet internal protrusions are intentionally omitted.
ring('Metal E-mount rear seating flange',29.8,25.0,1.5,(-.75,0,0),silver,'x',128)
ring('Rear mount rubber seal',30.8,29.8,.8,(-1.8,0,0),rubber,'x',128)
ring('Rear optical retaining ring',25.0,18.0,1.5,(-2.2,0,0),edge,'x',96)
cyl('Rear optical element',18,.35,(-3.0,0,0),sensor,'x',96,.1)
for i in range(10):
    a=math.radians(210+i*5.1);cyl('Rear electronic contact '+str(i+1),.5,.4,(-.20,23*math.cos(a),23*math.sin(a)),gold,'x',16,.05)
# Front filter opening and shallow smooth front optical surface, no cap or hood.
ring('Front filter rim outer lip',39.0,36.0,.9,(-87.65,0,0),control,'x',192)
for xx in [-87.1,-86.3,-85.5]:ring('72 mm filter thread visual groove',36.0,35.65,.28,(xx,0,0),darksilver,'x',192)
ring('Front optical retaining bevel',35.55,30.7,1.2,(-82.2,0,0),edge,'x',128)
optic=material('Multi coated optical glass',(.012,.030,.040),.55,.10)
optic.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.65
optic.node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value=.08
lathe('Curved front glass surface',[(-85.4+3.2*(i/32)**2,30.7*i/32) for i in range(33)],optic,192)
# A darker internal optical reflection, visible through angle-dependent highlight.
ring('Inner lens annular reflection',22,20,.10,(-80.5,0,0),sensor,'x',128)
# Hood bayonet tabs are present, but the supplied removable hood is not installed.
for deg in [15,135,255]:
    a=math.radians(deg);o=box('Lens hood bayonet tab',(2.2,7.5,1.0),(-83.3,38.55*math.sin(a),38.55*math.cos(a)),control,.25);o.rotation_euler.x=-a
# Controls on photographer-left (-Y), preserving official relative layout.
def tangential_box(name,x,theta,r,dims,mat=control,bevel_r=.5):
    a=math.radians(theta);o=box(name,dims,(x,r*math.sin(a),r*math.cos(a)),mat,bevel_r);o.rotation_euler.x=math.radians(-theta-90);return o

def curved_text(name,string,x,theta,r,size,mat=white,align='CENTER'):
    a=math.radians(theta);cu=bpy.data.curves.new(name,'FONT');cu.body=string;cu.align_x=align;cu.align_y='CENTER';cu.size=size;cu.extrude=.012;cu.resolution_u=4
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=(x,r*math.sin(a),r*math.cos(a));o.rotation_euler.x=math.radians(-theta)
    cu.materials.append(mat);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');MODEL.append(bpy.context.object);return bpy.context.object

def radial_button(name,x,theta,r,diam,depth,mat):
    a=math.radians(theta);o=cyl(name,diam/2,depth,(x,r*math.sin(a),r*math.cos(a)),mat,'z',64,.3)
    o.rotation_euler.x=-a;return o
# G logo, rocker, focus hold and AF/MF selector form the distinctive side panel.
tangential_box('G badge recessed base',-42,-57,36.75,(9.8,1.0,6.7),edge,.9)
curved_text('G badge silver','G',-42,-57,37.55,5.4,white)
tangential_box('Power zoom rocker recessed slot',-42,-89,36.8,(8.8,1.0,19.8),edge,1.2)
tangential_box('Power zoom rocker',-42,-89,37.45,(6.5,1.8,16.0),control,1.1)
for xx in [-44,-42.6,-41.2,-39.8]:
    for zz in [-5.4,-3.6,-1.8,0,1.8,3.6,5.4]:
        o=box('Rocker grip diamond',(.9,.4,.9),(xx,-38.5,zz+.65),rubber,.1);o.rotation_euler.y=math.pi/4
curved_text('Zoom T mark','T',-35.7,-77,37.25,2.2)
curved_text('Zoom W mark','W',-35.7,-101,37.25,2.2)
radial_button('Focus hold bezel',-42,-124,37.0,12.0,1.1,edge)
radial_button('Focus hold button',-42,-124,37.8,9.2,1.1,control)
tangential_box('AF MF switch recess',-42,-145,37.0,(12,1.0,4.2),edge,.8)
tangential_box('AF MF slider',-43,-145,37.65,(4.5,1.0,3.0),control,.6)
curved_text('AF MF legend','AF | MF',-42,-137,37.4,1.7)
# Opposite-side click and iris lock controls (closed/fixed visual positions).
tangential_box('Aperture click switch pocket',-24,93,36.7,(10,1.0,5.1),edge,.8)
tangential_box('Aperture click switch slider',-25,93,37.4,(4.6,1.0,3.5),control,.5)
curved_text('Click legend','CLICK',-24,80,37.2,1.8)
tangential_box('Iris lock switch pocket',-17,48,33.6,(7.0,1.0,4.6),edge,.7)
tangential_box('Iris lock switch slider',-17,48,34.3,(3.0,1.0,3.2),control,.4)
curved_text('Iris lock legend','IRIS LOCK',-17,33,34.6,1.5)
# Printed model name on the upper barrel, aperture scale wraps around rear ring.
curved_text('Lens model name','FE PZ 4/16-35 G',-42,-8,36.9,2.8)
curved_text('Sony barrel wordmark','SONY',-7.5,-5,30.9,3.0)
curved_text('Lens SKU','SELP1635G',-7.5,95,30.9,1.7)
for text_value,deg in [('4',3),('5.6',-14),('8',-31),('11',-48),('16',-65),('22',-82),('A',-100)]:
    curved_text('Aperture '+text_value,text_value,-24.0,deg,37.05,2.0,red if text_value=='A' else white)
for deg in range(-101,5,6):
    tangential_box('Aperture tick',-26.0,deg,37.05,(.5,.1,.55),white,.04)
curved_text('Fixed aperture index','|',-19.6,-100,36.2,2.4,white)
# Mount alignment marker is a painted dot on the rear neck.
radial_button('White E mount index',-5.5,-91,30.65,2.2,.22,white)
curved_text('E mount legend','E-mount',-5.5,-113,31.0,1.5)
# Thin front face lettering, localized around top and bottom of filter ring.
def face_text(name,string,x,y,z,size):
    cu=bpy.data.curves.new(name,'FONT');cu.body=string;cu.align_x='CENTER';cu.size=size;cu.extrude=.008;cu.resolution_u=4
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=(x,y,z)
    o.rotation_euler=Matrix(((0,0,-1),(-1,0,0),(0,1,0))).to_euler();cu.materials.append(white)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');MODEL.append(bpy.context.object)
face_text('Front lens identity','FE PZ 4/16-35 G',-88.08,0,36.0,1.35)
face_text('Front filter diameter','Ø72',-88.08,0,-37.0,1.4)
# Apply geometry transforms. Cap tiny decoration to the verified maximum diameter.
for o in MODEL:
    bpy.context.view_layer.objects.active=o
    for mod in list(o.modifiers):
        try:bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception:pass
    matrix=o.matrix_world.copy()
    for v in o.data.vertices:
        v.co=matrix@v.co
    o.matrix_world=Matrix.Identity(4)
root=bpy.data.objects.new('Sony_SELP1635G_visual_reference_mm_Zup',None);bpy.context.collection.objects.link(root)
root['units']='millimeters';root['axis']='-X';root['mount_flange_origin_mm']=[0,0,0];root['fidelity']='Official envelope, photo estimated external profile; not OEM CAD'
for o in MODEL:o.parent=root
bpy.context.view_layer.update()
coords=[v.co for o in MODEL for v in o.data.vertices]
mins=[min(v[k] for v in coords) for k in range(3)];maxs=[max(v[k] for v in coords) for k in range(3)]
# Metric requested by the assembly author: clip every triangle against the cover-top plane.
zplane=-35.86041180505664
clipped_points=[];tri_count=0
for o in MODEL:
    o.data.calc_loop_triangles();tri_count+=len(o.data.loop_triangles)
    for tri in o.data.loop_triangles:
        vs=[o.data.vertices[i].co.copy() for i in tri.vertices]
        for a in vs:
            if a.z<=zplane+1e-9:clipped_points.append(a)
        for i in range(3):
            a,b=vs[i],vs[(i+1)%3]
            if (a.z-zplane)*(b.z-zplane)<0:
                clipped_points.append(a+(b-a)*((zplane-a.z)/(b.z-a.z)))
max_below=max(p.x for p in clipped_points)
body_offset=-24.724525213241577;hole_x=-112;cover_min=-150.3394
world_max=hole_x+body_offset+max_below
meta={
 'title':'Sony FE PZ 16-35mm F4 G', 'model':'SELP1635G','created':'2026-11-23',
 'provenance':'Original procedural visual reconstruction from official Sony specification and reference photos. Not manufacturer CAD or a measured scan.',
 'verified_specs':{'maximum_diameter_mm':80.5,'length_mm':88.1,'mass_g':353,'filter_diameter_mm':72,'mount':'Sony E','focal_length_mm':[16,35],'maximum_aperture_f':4,'length_constant_while_focusing_and_zooming':True},
 'coordinates':{'units':'millimeters','up_axis':'Z','optical_axis_direction':[-1,0,0],'origin':'rear flange mounting plane and optical axis; X0,Y0,Z0','gltf_note':'Intentional viewer-native mm/Z-up, no meter scaling or axis conversion.'},
 'bounds_mm':{'min':mins,'max':maxs},'max_radial_mm':max(math.hypot(v.y,v.z) for v in coords),
 'axial_profile_visual_estimate_mm':profile[:17],
 'lens_state':{'hood_installed':False,'front_cap_installed':False,'rear_cap_installed':False,'internal_bayonet_protrusions_modeled':False},
 'fit_metric':{'method':'Exact triangle clipping against local horizontal plane, retaining vertices and edge-plane intersections. Conservative sufficient nonintersection condition with entire cover minimum X.','plane_local_z_mm':zplane,'max_local_x_at_or_below_plane_mm':max_below,'proposed_camera_hole_x_mm':hole_x,'body_flange_local_x_mm':body_offset,'cover_min_x_mm':cover_min,'max_world_x_below_cover_top_mm':world_max,'conservative_front_clearance_mm':cover_min-world_max,'validity':'Only for this photo-estimated geometry and proposed pose; not a physical fit guarantee.'},
 'assembly_attachment':{'body_flange_local_mm':[-24.724525213241577,0,35.86041180505664],'rotation_radians':[0,0,0],'scale':[1,1,1]},
 'limitations':['Verified overall diameter and nominal length; detailed axial stations and control locations estimated from official photos.','Mounting flange is a placement datum, not validated bayonet geometry.','No optical prescription, mechanical tolerances, printability or physical clearance validation.','Sony body tripod XY remains unverified.','Hood and caps intentionally omitted.'],
 'sources':[{'url':'https://www.sony.com/electronics/support/lenses-e-mount-lenses/selp1635g/specifications','use':'verified dimensions, mass, filter and model specs'},{'url':'https://www.sony-asia.com/lenses/products/selp1635g/feature1','use':'constant length, three control rings and power-zoom controls'},{'url':'https://sony.scene7.com/is/image/sonyglobalsolutions/Dimensions-image-2?fmt=png-alpha&wid=1600','local':'references/official-dimensions.png','use':'profile and side controls'},{'url':'https://sony.scene7.com/is/image/sonyglobalsolutions/m-feature-5-21?fmt=png-alpha&wid=1600','local':'references/official-three-rings.png','use':'detailed ring and control appearance'}],
 'mesh':{'objects':len(MODEL),'triangles':tri_count},'exports':['sony-selp1635g.glb','sony-selp1635g.stl']}
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in MODEL:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/'sony-selp1635g.glb'),export_format='GLB',use_selection=True,export_yup=False,export_extras=True,export_apply=True,export_cameras=False,export_lights=False,export_materials='EXPORT')
with open(OUT/'sony-selp1635g.stl','wb') as f:
    f.write(b'SELP1635G visual reference | mm Zup lens-X | not OEM CAD'.ljust(80,b' '));f.write(struct.pack('<I',tri_count))
    for o in MODEL:
        for tri in o.data.loop_triangles:
            a,b,c=[o.data.vertices[i].co for i in tri.vertices];n=(b-a).cross(c-a).normalized();f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
for filename in meta['exports']:
    p=OUT/filename;meta.setdefault('files',{})[filename]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(OUT/'sony-selp1635g.json').write_text(json.dumps(meta,indent=2)+'\n');(HERE/'model-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
print('LENS_EXPORT_DONE '+json.dumps(meta['fit_metric']),flush=True)
# Three studio views, preserving axis-centered model exports.
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.color=(.1,.1,.1);scene.view_settings.view_transform='AgX'
floor_mat=material('Studio grey',(.20,.23,.26),0,.85)
bpy.ops.mesh.primitive_plane_add(size=2000,location=(-40,0,-40.6));floor=bpy.context.object;floor.name='QA ground only';floor.data.materials.append(floor_mat)
def area(name,loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((-40,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
area('Main softbox',(-180,-180,190),450000,140);area('Fill softbox',(-100,120,130),250000,130);area('Rim softbox',(100,0,160),350000,130)
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=150;cam.data.clip_start=.1;cam.data.clip_end=2000
for name,loc in [('front-three-quarter',(-220,-220,130)),('controls-side',(-44,-300,10)),('front',(-350,0,0))]:
    cam.location=loc;cam.rotation_euler=(Vector((-44,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PREVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'sony-selp1635g.blend'))
print('LENS_MODEL_DONE '+json.dumps(meta['mesh']),flush=True)
