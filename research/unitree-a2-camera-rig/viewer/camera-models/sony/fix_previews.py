from pathlib import Path
import bpy,math
from mathutils import Vector
here=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(here/'sony-zv-e1.blend'))
scene=bpy.context.scene;cam=scene.camera
for name,loc,target in [('front-three-quarter',(-230,205,155),(-8,12.5,35)),('rear-three-quarter',(230,-160,145),(-8,12.5,35)),('front',(-280,12.5,37),(-8,12.5,36)),('top',(-5,12.5,300),(-5,12.5,36))]:
    cam.location=loc;cam.data.ortho_scale=176
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    if name=='top':cam.rotation_euler=(0,0,math.pi/2);cam.data.ortho_scale=156
    scene.render.filepath=str(here/'previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(here/'sony-zv-e1.blend'))
