"""Render selected saved cameras and audit the native Blender deliverable."""
import bpy, os, sys, json, math
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scene=bpy.context.scene
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
frames=[int(a) for a in args if a.isdigit()] or [1,2,3]
draft='--draft' in args
scene.render.resolution_percentage=55 if draft else 100
scene.cycles.samples=16 if draft else 64
scene.cycles.use_denoising=True
scene.cycles.adaptive_threshold=.035
pref=bpy.context.preferences.addons['cycles'].preferences
try:
    pref.compute_device_type='METAL';pref.get_devices()
    for d in pref.devices:d.use=d.type=='METAL'
    if any(d.type=='METAL' for d in pref.devices):scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
names={1:'01_pool_hero',2:'02_pool_terrace',3:'03_street_entrance',4:'04_aerial'}
audit={
    'blend_file':bpy.data.filepath,
    'objects':len(scene.objects),
    'mesh_objects':sum(o.type=='MESH' for o in scene.objects),
    'cameras':sum(o.type=='CAMERA' for o in scene.objects),
    'collections':len(scene.collection.children),
    'missing_images':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not os.path.exists(bpy.path.abspath(i.filepath))],
    'invalid_transforms':[o.name for o in scene.objects if any(not math.isfinite(v) for row in o.matrix_world for v in row)],
    'empty_meshes':[o.name for o in scene.objects if o.type=='MESH' and not o.data.vertices],
    'camera_markers':{m.frame:m.camera.name for m in scene.timeline_markers if m.camera},
    'renders':[]
}
assert not audit['missing_images'],audit['missing_images']
assert not audit['invalid_transforms'],audit['invalid_transforms']
assert not audit['empty_meshes'],audit['empty_meshes']
for frame in frames:
    scene.frame_set(frame)
    scene.camera=next(m.camera for m in scene.timeline_markers if m.frame==frame)
    scene.render.filepath=os.path.join(ROOT,'renders',names[frame]+('_draft' if draft else '')+'.png')
    print('RENDERING',frame,scene.camera.name,flush=True)
    bpy.ops.render.render(write_still=True)
    audit['renders'].append(scene.render.filepath)
with open(os.path.join(ROOT,'renders','validation.json'),'w') as f:json.dump(audit,f,indent=2)
print('AUDIT',json.dumps(audit),flush=True)
