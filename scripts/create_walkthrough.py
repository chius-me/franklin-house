"""Build and render a 15-second real 3D camera tour; preserve the still project."""
import bpy, os, sys, time, json
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'video')
os.makedirs(os.path.join(OUT,'frames'),exist_ok=True)
scene=bpy.context.scene
scene.timeline_markers.clear()
scene.frame_start=1;scene.frame_end=360
scene.render.fps=24;scene.render.fps_base=1
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.engine='CYCLES'
scene.cycles.samples=16;scene.cycles.adaptive_threshold=.09;scene.cycles.use_denoising=True
scene.cycles.use_animated_seed=False
scene.render.use_persistent_data=True
scene.render.film_transparent=False
pref=bpy.context.preferences.addons['cycles'].preferences
try:
    pref.compute_device_type='METAL';pref.get_devices()
    for d in pref.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU' if any(d.use for d in pref.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
collection=bpy.data.collections.new('12 · Camera walkthrough');scene.collection.children.link(collection)
shots=[
    ('01 · Villa reveal',1,120,(25,-49,20),(0,-49,17.5),(1.8,-1.8,2.1),39),
    ('02 · Pool promenade',121,240,(17,-26,9),(3,-26,7.8),(.8,-2,2.4),29),
    ('03 · Street arrival',241,360,(25,25,10),(15,26,8.7),(4.0,8.0,4.5),29),
]
for name,first,last,start,end,target,lens in shots:
    data=bpy.data.cameras.new(name);data.lens=lens;data.clip_end=500
    camera=bpy.data.objects.new(name,data);collection.objects.link(camera)
    focus=bpy.data.objects.new(name+' / look-at',None);collection.objects.link(focus);focus.location=target
    track=camera.constraints.new('TRACK_TO');track.target=focus;track.track_axis='TRACK_NEGATIVE_Z';track.up_axis='UP_Y'
    for frame,loc in [(first,start),(last,end)]:
        camera.location=loc;camera.keyframe_insert(data_path='location',frame=frame)
    # Blender's default Bézier interpolation gives gentle acceleration and deceleration.
    marker=scene.timeline_markers.new(name,frame=first);marker.camera=camera
scene.frame_set(1);scene.camera=next(m.camera for m in scene.timeline_markers if m.frame==1)
scene.render.filepath=os.path.join(OUT,'frames','frame_')
scene['video_notes']='Three genuine camera moves; 1280x720, 24 fps, 15 seconds. Original still .blend preserved.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Franklin_Walkthrough.blend'))
if '--preview' in sys.argv:
    times=[]
    scene.render.resolution_percentage=75
    for frame in (1,120,121,240,241,360):
        scene.frame_set(frame)
        scene.render.filepath=os.path.join(OUT,'preview_%03d.png'%frame)
        begin=time.time();bpy.ops.render.render(write_still=True)
        times.append({'frame':frame,'seconds':round(time.time()-begin,2)})
    print('PREVIEW_TIMES',json.dumps(times),flush=True)
elif '--render' in sys.argv:
    bpy.ops.render.render(animation=True)
