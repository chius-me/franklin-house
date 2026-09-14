"""Encode the complete frame sequence to a browser-compatible MP4 and verify it."""
import os, json, subprocess
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'video')
for frame in range(1,361):
    path=os.path.join(OUT,'frames','frame_%04d.png'%frame)
    if not os.path.exists(path) or os.path.getsize(path)<1024:
        raise RuntimeError('Missing or incomplete rendered frame: '+path)
video=os.path.join(OUT,'Franklin_Villa_Walkthrough.mp4')
filters=(
    '[0:v]split=3[a][b][c];'
    '[a]trim=start_frame=0:end_frame=120,setpts=PTS-STARTPTS[s1];'
    '[b]trim=start_frame=120:end_frame=240,setpts=PTS-STARTPTS[s2];'
    '[c]trim=start_frame=240:end_frame=360,setpts=PTS-STARTPTS[s3];'
    '[s1][s2]xfade=transition=fade:duration=0.5:offset=4.5[x];'
    '[x][s3]xfade=transition=fade:duration=0.5:offset=9.0,'
    'fade=t=out:st=13.5:d=0.5,format=yuv420p[v]'
)
subprocess.run([
    '/opt/homebrew/bin/ffmpeg','-hide_banner','-y','-framerate','24',
    '-start_number','1','-i',os.path.join(OUT,'frames','frame_%04d.png'),
    '-filter_complex',filters,'-map','[v]','-an','-c:v','libx264',
    '-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','24',
    '-movflags','+faststart','-metadata','title=Franklin | 3671 Whispymound Drive',video
],check=True)
probe=json.loads(subprocess.check_output([
    '/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',video
]))
stream=next(s for s in probe['streams'] if s['codec_type']=='video')
assert stream['codec_name']=='h264'
assert (stream['width'],stream['height'])==(1280,720)
assert stream['pix_fmt']=='yuv420p'
assert 13.9<=float(probe['format']['duration'])<=14.1
subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-i',video,'-f','null','-'],check=True)
with open(os.path.join(OUT,'video_validation.json'),'w') as f:json.dump(probe,f,indent=2)
print('VERIFIED',video)
