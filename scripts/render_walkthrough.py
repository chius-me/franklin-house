"""Resume PNG sequence rendering from the animated project."""
import bpy, os, sys, time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scene=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences
try:
    pref.compute_device_type='METAL';pref.get_devices()
    for d in pref.devices:d.use=d.type=='METAL'
    if any(d.use for d in pref.devices):scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
scene.render.use_persistent_data=True
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
start=int(args[0]) if args else 1
stop=int(args[1]) if len(args)>1 else 360
for frame in range(start,stop+1):
    path=os.path.join(ROOT,'video','frames','frame_%04d.png'%frame)
    if os.path.exists(path):continue
    scene.frame_set(frame);scene.render.filepath=path
    t=time.time();bpy.ops.render.render(write_still=True)
    print('FRAME',frame,'SECONDS',round(time.time()-t,2),flush=True)
