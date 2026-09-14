"""Franklin's Vinewood Hills house — editable reference-based reconstruction.
Run: Blender --background --python scripts/build_franklin.py
No external assets, addons or texture dependencies are required.
"""
import bpy, math, random, os, json, sys
from mathutils import Vector
from math import sin, cos, pi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(3671)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
default = bpy.data.collections.get('Collection')
if default: bpy.data.collections.remove(default)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
collections = {}
def group(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    collections[name] = c
    return c
SITE = group('01 · Hillside & street')
STRUCT = group('02 · Concrete structure')
FACADE = group('03 · Stone, timber & roof')
GLASS = group('04 · Windows & balcony balustrades')
POOL = group('05 · Infinity pool & spa')
DECK = group('06 · Terraces & outdoor furniture')
INTERIOR = group('07 · Living room, kitchen & bedroom')
GARDEN = group('08 · Planting & trees')
DETAIL = group('09 · Entrance & architectural details')
LIGHT = group('10 · Lighting')
CAMS = group('11 · Cameras')

def material(name, color, rough=.5, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color,1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    return m

def noise_mat(name, low, high, scale=4, rough=.65, bump=.08, mapping=(1,1,1)):
    m = material(name, low, rough)
    n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexCoord'); v=n.new('ShaderNodeVectorMath'); v.operation='MULTIPLY'
    v.inputs[1].default_value=mapping; l.new(tex.outputs['Object'],v.inputs[0])
    noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=scale
    noise.inputs['Detail'].default_value=3; noise.inputs['Roughness'].default_value=.7
    l.new(v.outputs[0],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.2
    ramp.color_ramp.elements[0].color=(*low,1); ramp.color_ramp.elements[1].position=.8
    ramp.color_ramp.elements[1].color=(*high,1)
    l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs[0],p.inputs['Base Color'])
    b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.3;b.inputs['Distance'].default_value=bump
    l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
    return m

concrete=noise_mat('Warm ivory / sand-finished concrete',(.32,.30,.25),(.57,.54,.46),32,bump=.025)
plaster=noise_mat('Limestone plaster',(.39,.37,.30),(.66,.63,.52),48,bump=.014)
roof=noise_mat('Weathered graphite roofing',(.016,.019,.017),(.068,.071,.059),5,bump=.045)
wood=noise_mat('Western red cedar · horizontal grain',(.060,.016,.006),(.22,.078,.018),3,bump=.028,mapping=(.25,5,8))
deckwood=[noise_mat('Teak boards %02d'%i,(.10+i*.008,.036+i*.004,.011+i*.002),(.27+i*.010,.12+i*.007,.034+i*.003),3,bump=.015,mapping=(.4,18,5)) for i in range(5)]
dark=material('Anodized charcoal aluminium',(.038,.05,.052),.29,.68)
steel=material('Brushed stainless steel',(.48,.54,.56),.22,.85)
black=material('Soft black',(.015,.019,.018),.42)
white=material('Warm white upholstery',(.82,.80,.70),.88)
blue=material('Indigo umbrella canvas',(.045,.085,.35),.8)
blue2=material('Indigo umbrella alternate panels',(.07,.13,.46),.8)
red=material('Terracotta accent upholstery',(.43,.085,.034),.82)
grass=noise_mat('Close-cut lawn',(.085,.14,.027),(.20,.29,.061),12,bump=.027)
earth=noise_mat('California hillside · earth & scrub',(.030,.045,.009),(.19,.18,.065),.6,bump=.21)
asphalt=noise_mat('Weathered asphalt',(.075,.08,.081),(.145,.15,.14),40,bump=.04)
soil=noise_mat('Planter potting soil',(.045,.031,.017),(.11,.076,.04),10,bump=.04)
stone_mats=[noise_mat('Split-face stone %02d'%i,(.090+i*.019,.095+i*.018,.075+i*.016),(.22+i*.025,.23+i*.023,.19+i*.021),8,bump=.07) for i in range(6)]
leaves=[material('Foliage %02d'%i,c,.8) for i,c in enumerate([(.075,.14,.029),(.12,.22,.045),(.19,.28,.064),(.045,.10,.021),(.25,.32,.084)])]
bark=noise_mat('Tree bark',(.10,.07,.036),(.25,.19,.11),7,bump=.10,mapping=(5,5,.7))
glass=material('Architectural glass · slight blue tint',(.72,.85,.87),.075)
p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.45
railglass=material('Balustrade glass',(.72,.87,.86),.07)
rp=railglass.node_tree.nodes.get('Principled BSDF');rp.inputs['Transmission Weight'].default_value=1;rp.inputs['IOR'].default_value=1.18
water=material('Pool water · procedural ripples',(.024,.32,.37),.085)
wp=water.node_tree.nodes.get('Principled BSDF');wp.inputs['Transmission Weight'].default_value=.7;wp.inputs['IOR'].default_value=1.333
wn=water.node_tree.nodes;wl=water.node_tree.links
tc=wn.new('ShaderNodeTexCoord');no=wn.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=3.5;no.inputs['Detail'].default_value=2
wl.new(tc.outputs['Object'],no.inputs['Vector']);bu=wn.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.23;bu.inputs['Distance'].default_value=.085
wl.new(no.outputs['Fac'],bu.inputs['Height']);wl.new(bu.outputs['Normal'],wp.inputs['Normal'])
tile=material('Pool mosaic · azure ceramic',(.10,.39,.42),.25)
tn=tile.node_tree.nodes;tl=tile.node_tree.links;tp=tn.get('Principled BSDF')
tco=tn.new('ShaderNodeTexCoord');br=tn.new('ShaderNodeTexBrick');br.inputs['Scale'].default_value=7
br.inputs['Color1'].default_value=(.06,.22,.26,1);br.inputs['Color2'].default_value=(.18,.44,.44,1)
br.inputs['Mortar'].default_value=(.30,.48,.47,1);br.inputs['Mortar Size'].default_value=.012
br.inputs['Brick Width'].default_value=.5;br.inputs['Row Height'].default_value=.5;br.offset=0
tl.new(tco.outputs['Object'],br.inputs['Vector']);tl.new(br.outputs['Color'],tp.inputs['Base Color'])

def obj(name, verts, faces, mat, coll):
    mesh=bpy.data.meshes.new(name+' · mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);coll.objects.link(o)
    if mat:o.data.materials.append(mat)
    return o
def bevel(o, amount=.025, segments=2):
    if amount:
        mod=o.modifiers.new('Soft architectural edges','BEVEL');mod.width=amount;mod.segments=segments
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def box(name,loc,size,mat,coll=STRUCT,b=.02,rot=0):
    x,y,z=[v/2 for v in size]
    o=obj(name,[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)],[(2,6,4,0),(5,7,3,1),(4,5,1,0),(3,7,6,2),(1,3,2,0),(6,7,5,4)],mat,coll)
    o.location=loc;o.rotation_euler[2]=rot
    return bevel(o,b)
def prism(name,poly,z0,z1,mat,coll=STRUCT,b=.02):
    n=len(poly);v=[(x,y,z0) for x,y in poly]+[(x,y,z1) for x,y in poly]
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return bevel(obj(name,v,f,mat,coll),b)
def cylinder(name,loc,radius,depth,mat,coll=DECK,vertices=24,r2=None):
    if r2 is None:r2=radius
    vs=[(radius*cos(i*2*pi/vertices),radius*sin(i*2*pi/vertices),-depth/2) for i in range(vertices)]+[(r2*cos(i*2*pi/vertices),r2*sin(i*2*pi/vertices),depth/2) for i in range(vertices)]
    f=[tuple(reversed(range(vertices))),tuple(range(vertices,2*vertices))]+[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    o=obj(name,vs,f,mat,coll);o.location=loc
    for p in o.data.polygons:
        if len(p.vertices)==4:p.use_smooth=True
    return o
def beam(name,a,b,width,mat,coll=STRUCT,depth=None):
    d=Vector(b)-Vector(a);o=box(name,(Vector(a)+Vector(b))/2,(width,depth or width,d.length),mat,coll,b=.009)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def pipe(name,points,r,mat,coll=DECK):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,cu);coll.objects.link(o);o.data.materials.append(mat);return o
def globe(name,loc,size,mat,coll=GARDEN,sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc)
    o=bpy.context.object;o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    coll.objects.link(o);o.scale=size;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o
def text_obj(name,body,loc,size,mat,rot=(pi/2,0,0),coll=DETAIL):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=.005;cu.space_character=1.1
    o=bpy.data.objects.new(name,cu);coll.objects.link(o);o.location=loc;o.rotation_euler=rot;cu.materials.append(mat);return o

# The hillside falls toward the negative Y pool elevation. Street is at upper-floor level.
def terrain_z(x,y):
    z=-4.1+.22*(y+13)+.0017*x*x
    if y>20:z+=.22*(y-20)
    z+=.55*sin(x*.15+y*.08)*cos(y*.21)+.20*sin(x*.48)*sin(y*.32)
    if -21<x<22 and -15<y<12:z=min(z,-1.8 if y<0 else -.1)
    if 8<y<26:
        road_weight=max(0,min(1,(y-8)/2,(26-y)/5))*max(0,min(1,(48-abs(x))/8))
        road_weight=road_weight*road_weight*(3-2*road_weight)
        z=z*(1-road_weight)+3.55*road_weight
    if -15.5<x<20 and -23<y<-1:
        z=max(z,-1.66-.18*max(0,-y-12.5)**2)
    return z
verts=[];faces=[];N=121
for j in range(N):
    y=-65+j*1.5
    for i in range(N):
        x=-90+i*1.5;verts.append((x,y,terrain_z(x,y)))
for j in range(N-1):
    for i in range(N-1):
        a=j*N+i;faces.append((a,a+1,a+N+1,a+N))
terrain=obj('Sculpted Vinewood hillside',verts,faces,earth,SITE)
for p in terrain.data.polygons:p.use_smooth=True
box('Whispymound Drive', (0,17,3.64),(90,7,.18),asphalt,SITE,.02)
box('Pavement apron',(2,11.8,3.65),(39,3.4,.23),concrete,SITE)
for x in range(-42,44,6):box('Road center marking',(x,17.2,3.743),(2.5,.10,.012),white,SITE,0)
for x in range(-42,44,3):
    box('Road curb',(x,13.45,3.81),(2.96,.26,.25),concrete,SITE)
for x in (-26,-23,-20,23,26,29):box('Red curb',(x,13.31,3.87),(2.96,.025,.10),red,SITE,.002)

# Slabs: a shallow kink in the long facade matches the original silhouette.
footprint=[(-13,-1.25),(-6,0),(9,0),(9,9.5),(-13,9.5)]
balcony=[(-14,-3.75),(-6,-2.45),(9.8,-2.45),(12,-.1),(20,-.1),(20,3.8),(9.5,3.8),(9.5,9.9),(-14,9.9)]
roofpoly=[(-14,-2.25),(-6,-1.05),(9.85,-1.05),(9.85,10),(-14,10)]
prism('Lower foundation',footprint,-1.1,-.02,concrete)
prism('Upper floor slab',footprint,3.36,3.67,concrete)
prism('Wraparound balcony slab',balcony,3.35,3.60,wood)
prism('Continuous roof / cedar soffit',roofpoly,6.93,7.15,wood,FACADE)
prism('Roof graphite fascia',roofpoly,7.15,7.40,roof,FACADE)
roofinner=[(-13.7,-1.95),(-6,-.75),(9.55,-.75),(9.55,9.7),(-13.7,9.7)]
prism('Recessed flat roof finish',roofinner,7.39,7.43,roof,FACADE)
box('Rear retaining wall',(-2,9.4,1.7),(22,.35,3.5),concrete)
box('Upper street wall',(-3,9.23,5.27),(20,.32,3.20),plaster)
box('West return wall',(-12.92,4.35,1.65),(.25,10.5,3.3),plaster)
box('West upper return wall',(-12.92,4.35,5.25),(.25,10.5,3.2),plaster)
box('East end wall',(8.85,5.2,1.65),(.30,8.4,3.3),plaster)
box('East upper end wall',(8.85,5.2,5.25),(.30,8.4,3.2),plaster)
box('Bedroom dividing wall',(1.5,4.5,1.66),(.18,8.8,3.3),plaster,INTERIOR)
box('Upper warm oak floor',(-1.8,4.5,3.7),(21.9,8.9,.06),deckwood[2],INTERIOR,.004)
box('Lower limestone floor',(-1.6,4.4,.01),(22,8.8,.06),concrete,INTERIOR,.003)

def stone_panel(name,a,b,z0,z1):
    a,b=Vector(a),Vector(b);v=b-a;L=v.length;t=v.normalized();normal=Vector((t.y,-t.x,0))
    center=(a+b)/2;center.z=(z0+z1)/2
    base=box(name+' / backing',center,(L,.23,z1-z0),stone_mats[0],FACADE,.01,math.atan2(t.y,t.x))
    z=z0;row=0
    while z<z1-.05:
        h=min(random.uniform(.30,.55),z1-z);x=0
        while x<L-.035:
            w=min(random.uniform(.4,.95),L-x)
            c=a+t*(x+w/2)+normal*.135;c.z=z+h/2
            # Uneven polygonal edges avoid an overly regular brick-pattern facade.
            ww=max(.04,w-.025)/2;hh=(h-.026)/2;th=random.uniform(.10,.18)
            outline=[(-ww,-hh),(-ww*.12,-hh+random.uniform(-.022,.022)),(ww,-hh*.77),(ww,hh*.70),(ww*.32,hh),(-ww*.66,hh*.94),(-ww,hh*.45)]
            sv=[(xx,yy,zz) for yy in (-th/2,th/2) for xx,zz in outline];sn=len(outline)
            sf=[tuple(range(sn)),tuple(reversed(range(sn,2*sn)))]+[(k,k+sn,(k+1)%sn+sn,(k+1)%sn) for k in range(sn)]
            o=obj(name+' / individual split stone',sv,sf,random.choice(stone_mats),FACADE);o.location=c;o.rotation_euler[2]=math.atan2(t.y,t.x);bevel(o,.016)
            x+=w
        z+=h;row+=1

# Heavy natural stone piers punctuate the curtain wall.
for x,w in [(-6.05,1.4),(2.75,.72),(8.5,.9)]:
    stone_panel('Facade stone pier', (x-w/2,0,0),(x+w/2,0,0),.02,6.94)
stone_panel('West stone return',(-13,-1.25,0),(-13,1.8,0),.04,6.94)
stone_panel('Eastern retaining room',(16.8,1.25,0),(20,1.25,0),0,3.4)
box('Eastern support room',(18.4,3,1.65),(3.2,3.5,3.3),stone_mats[2])

def glazing(name,a,b,z0,z1,n=4):
    a,b=Vector(a),Vector(b);v=b-a;t=v.normalized();angle=math.atan2(v.y,v.x);L=v.length
    for j in range(n):
        c=a+t*(L*(j+.5)/n);c.z=(z0+z1)/2
        box(name+' / glass %02d'%j,c,(L/n-.065,.034,z1-z0-.10),glass,GLASS,.003,angle)
    for j in range(n+1):
        c=a+t*(L*j/n);c.z=(z0+z1)/2
        box(name+' / mullion',c,(.055,.095,z1-z0),dark,GLASS,.005,angle)
    for z in (z0,z1):
        c=(a+b)/2;c.z=z;box(name+' / track',c,(L,.10,.065),dark,GLASS,.008,angle)
    # paired stainless handles on the central sliding panel
    for k in (-.10,.10):
        c=(a+b)/2+t*k+Vector((t.y,-t.x,0))*.1;c.z=z0+1.2
        box(name+' / sliding door pull',c,(.025,.04,.29),steel,GLASS,.006,angle)

for z0,z1 in [(0.08,3.30),(3.72,6.91)]:
    glazing('Long living / bedroom window',(-5.35,-.015,0),(2.36,-.015,0),z0,z1,4)
    glazing('East sliding glazing',(3.16,-.015,0),(8.03,-.015,0),z0,z1,3)
    glazing('Angled west glazing',(-12.85,-1.26,0),(-6.78,-.16,0),z0,z1,3)

def rail(name,pts,z,height=1.03):
    for a,b in zip(pts[:-1],pts[1:]):
        a=Vector((*a,z));b=Vector((*b,z));v=b-a;L=v.length;n=max(1,math.ceil(L/1.65));t=v.normalized();ang=math.atan2(v.y,v.x)
        for i in range(n):
            c=a+v*((i+.5)/n);c.z=z+height*.52
            box(name+' / glass',c,(L/n-.07,.027,height-.18),railglass,GLASS,.006,ang)
        for i in range(n+1):
            p=a+v*(i/n)
            cylinder(name+' / stanchion',(p.x,p.y,z+height/2),.023,height,steel,GLASS,12)
            box(name+' / base shoe',(p.x,p.y,z+.025),(.13,.13,.05),steel,GLASS,.006)
            for dz in (.22,height-.19):box(name+' / clamp',(p.x,p.y,z+dz),(.085,.07,.035),steel,GLASS,.004,ang)
        pipe(name+' / handrail',[(a.x,a.y,z+height),(b.x,b.y,z+height)],.027,steel,GLASS)

rail('Upper terrace railing',[(-13.85,2.5),(-13.85,-3.57),(-6,-2.28),(9.65,-2.28),(12,.07),(19.8,.07),(19.8,3.5)],3.62)
# Balcony floor boards laid along the elevation, trimmed to the footprint.
for i in range(11):
    y=-2.25+i*.195
    box('Upper balcony teak plank',(1.65,y,3.63),(15.7,.18,.055),random.choice(deckwood),FACADE,.006)
for i in range(11):
    # Follow the angled west wing instead of covering the terrace with a single slab.
    a=Vector((-13.7,-3.45+i*.195,3.63));b=Vector((-6,-2.17+i*.195,3.63))
    c=(a+b)/2;box('Angled balcony plank',c,((b-a).length,.18,.055),random.choice(deckwood),FACADE,.005,math.atan2((b-a).y,(b-a).x))
for x,y in [(-13.5,-3.28),(-6,-2.0),(9.6,-1.9),(13.7,.6),(19,.6)]:
    box('Cedar deck support post',(x,y,1.73),(.22,.22,3.4),wood,FACADE,.035)
for x,y in [(-13.4,-1.82),(9.42,-.65)]:box('Upper cedar roof post',(x,y,5.28),(.17,.17,3.4),wood,FACADE)
for i in range(34):
    y=-.5+i*.30
    box('Roof soffit slat',(-1.8,y,6.918),(22.9,.022,.025),dark,FACADE,.002)
# Six low-profile roof skylights, vents, and a chimney.
for x in (-10.5,-7.7,-4.9):
    for y in (5.5,7.4):
        box('Skylight curb',(x,y,7.5),(1.55,1.18,.17),dark,FACADE)
        box('Skylight pane',(x,y,7.60),(1.41,1.05,.034),glass,GLASS,.004)
for x in (-2.4,-1.7):
    cylinder('Roof vent',(x,6,7.75),.12,.65,steel,FACADE)
    cylinder('Vent cap',(x,6,8.07),.21,.08,dark,FACADE)
box('Roof flue',(5.7,8.6,7.8),(.9,.8,.8),stone_mats[2],FACADE)
box('Flue coping',(5.7,8.6,8.23),(1.1,1,.12),dark,FACADE)

print('Structure and glazing complete',flush=True)

# Garage and street entrance sit on the upper level at the right of the house.
box('Garage structural floor',(16,7.4,3.45),(8.1,7.8,.35),concrete)
box('Garage east wall',(20,7.4,5.20),(.26,7.8,3.2),plaster)
box('Garage west wall',(12,7.4,5.20),(.26,7.8,3.2),plaster)
box('Garage south wall',(16,3.6,5.20),(8,.25,3.2),plaster)
box('Garage roof',(16,7.4,6.95),(8.7,8.1,.25),roof,FACADE)
box('Garage roof edge',(16,11.46,6.92),(8.7,.15,.27),concrete,FACADE)
box('Garage north backing',(16,11.20,5.25),(8,.17,3.2),wood,FACADE)
for i in range(19):
    z=3.76+i*.163
    box('Garage cedar cladding south',(16,3.44,z),(8.15,.08,.15),random.choice(deckwood),FACADE,.008)
    box('Garage cedar cladding east',(20.17,7.4,z),(.08,7.8,.15),random.choice(deckwood),FACADE,.008)
    for x in (12.48,19.54):box('Garage cedar cladding door surround',(x,11.34,z),(.9,.08,.15),wood,FACADE,.006)
box('Garage overhead cedar lintel',(16,11.36,6.55),(6.8,.14,.69),wood,FACADE)
box('Double garage door',(16,11.40,5.06),(6.30,.10,2.65),dark,DETAIL,.035)
for x in [12.85+j*1.05 for j in range(7)]:box('Garage vertical frame',(x,11.47,5.06),(.045,.05,2.65),steel,DETAIL,.004)
for z in [3.74+j*.53 for j in range(6)]:box('Garage sectional rail',(16,11.47,z),(6.3,.055,.036),steel,DETAIL,.004)
for x in (14.7,17.3):box('Garage door pull',(x,11.51,4.93),(.28,.035,.055),steel,DETAIL,.006)
# Narrow clerestory along the back of the garage.
box('Garage clerestory dark surround',(16,3.34,6.12),(4.8,.045,.37),dark,DETAIL)
box('Garage clerestory glass',(16,3.30,6.12),(4.65,.026,.25),glass,GLASS,.004)
for x in (14.1,15.1,16.1,17.1,18.1):box('Clerestory frame',(x,3.28,6.12),(.032,.06,.28),steel,GLASS,.002)
box('Entrance portal left pier',(9.18,10.6,5.1),(.40,.26,2.9),plaster)
box('Entrance house-number wall',(11.0,10.6,5.1),(1.24,.26,2.9),plaster)
box('Entrance portal lintel',(10.0,10.6,6.62),(2.08,.3,.22),plaster)
box('Entry timber gate',(9.73,10.54,5.05),(.82,.075,2.5),wood,DETAIL,.012)
for i in range(9):box('Gate vertical slat',(9.38+i*.085,10.60,5.05),(.027,.045,2.47),dark,DETAIL,.002)
box('Entry gate handle',(10.04,10.68,5.0),(.033,.05,.32),steel,DETAIL,.01)
text_obj('House number / 3671','3671',(11.48,10.75,5.11),.33,dark,(pi/2,0,pi))
box('House nameplate',(11,10.76,4.90),(.71,.06,.15),wood,DETAIL,.015)
text_obj('House nameplate lettering','CLINTON',(11.30,10.8,4.88),.095,white,(pi/2,0,pi))
for i in range(6):box('Entry descending stair',(10.4,9.85-i*.39,3.62-i*.13),(2.2,.40,.16),concrete)
for i in range(9):
    z=6.09+i*.09
    box('Street elevation timber band',(-2.7,9.45,z),(20.3,.07,.078),wood,FACADE,.005)
stone_panel('Street-side stone cladding',(8.65,9.46,0),(-12.9,9.46,0),3.8,5.9)
# Narrow entrance landing and a cedar privacy screen at the western end.
box('Entry walkway',(6.8,10.5,3.72),(4.4,2.4,.14),concrete,DETAIL)
for x in (-14,-13.7,-13.4,-13.1):box('Privacy cedar fins',(x,7.7,5.23),(.14,3.4,3.05),wood,FACADE)

# Exterior stair links the upper balcony to the pool promenade.
for i in range(19):
    y=-3.5+i*.29;z=.10+i*(3.5/19)
    box('Pool terrace stair / tread %02d'%i,(10.7,y,z),(1.35,.305,.11),concrete,STRUCT,.018)
for x in (10.05,11.35):
    beam('Stair steel stringer',(x,-3.67,-.02),(x,1.88,3.50),.14,dark)
    pipe('Stair continuous handrail',[(x,-3.65,1.0),(x,1.93,4.53)],.028,steel,GLASS)
    for i in (0,4,8,12,18):
        y=-3.5+i*.29;z=.10+i*(3.5/19)
        cylinder('Stair railing post',(x,y,z+.50),.024,1.,steel,GLASS,12)
box('Stair upper landing',(10.7,2.38,3.56),(1.6,1.25,.16),concrete)

# Terraces and true open pool basin, with water and individual coping stones.
box('Pool promenade slab',(1.4,-4.2,-.20),(34.0,4.35,.40),concrete)
box('East deck retaining plinth',(14.8,-9.9,-.96),(8.1,6.4,1.9),concrete)
box('West lawn terrace support',(-10.3,-8.9,-.76),(7.4,8.0,1.5),roof)
box('Cantilever lawn terrace cedar edge',(-10.3,-8.9,-.02),(7.5,8.1,.24),wood,FACADE)
box('West lawn terrace',(-10.3,-9.2,.13),(7.1,7.2,.17),grass,DECK)
rail('Lawn terrace balustrade',[(-13.8,-5.6),(-13.8,-12.85),(-6.75,-12.85)],.16,.96)
for ix in range(34):
    for iy in range(3):
        x=-14.65+ix*.985;y=-5.75+iy*1.12
        if 10<x<11.5 and y>-4:continue
        box('Pool promenade limestone paving',(x,y,.031),(.967,1.10,.045),concrete,DECK,.006)
# Terracotta strip between house and pool.
terracotta=[noise_mat('Terracotta paving %02d'%i,(.19+i*.012,.115+i*.008,.066+i*.006),(.34+i*.012,.23+i*.008,.135+i*.009),8,bump=.025) for i in range(3)]
for ix in range(36):
    for iy in range(2):box('Terracotta border tile',(-5.98+ix*.46,-6.12+iy*.43,.046),(.445,.413,.048),random.choice(terracotta),DECK,.004)
px0,px1,py0,py1=-6.48,10.64,-12.9,-6.65
box('Pool basin floor',((px0+px1)/2,(py0+py1)/2,-1.52),(px1-px0,py1-py0,.20),tile,POOL)
for name,loc,sz in [
    ('Pool west wall',(px0,(py0+py1)/2,-.79),(.22,py1-py0,1.50)),
    ('Pool east wall',(px1,(py0+py1)/2,-.79),(.22,py1-py0,1.50)),
    ('Pool house-side wall',((px0+px1)/2,py1,-.79),(px1-px0,.22,1.50)),
    ('Infinity overflow wall',((px0+px1)/2,py0,-.85),(px1-px0,.18,1.34))]:box(name,loc,sz,tile,POOL,.015)
box('Pool water surface',((px0+px1)/2,(py0+py1)/2,-.18),(px1-px0-.22,py1-py0-.20,.065),water,POOL,.012)
for i in range(4):box('Submerged broad entry step',(-5.88+i*.30,-7.8,-.29-i*.28),(.50,2.0,.24),tile,POOL,.015)
for i in range(29):
    x=px0+(i+.5)*(px1-px0)/29
    box('Northern coping stone',(x,py1+.16,.023),((px1-px0)/29-.012,.40,.13),plaster,POOL,.012)
    box('Infinity edge coping',(x,py0,-.118),((px1-px0)/29-.012,.22,.09),plaster,POOL,.012)
for x in (px0-.10,px1+.1):
    for i in range(11):box('Side coping stone',(x,py0+.28+i*.55,.015),(.35,.538,.14),plaster,POOL,.012)
box('Infinity overflow catch basin',((px0+px1)/2,py0-.35,-.53),(px1-px0+.6,.50,.16),tile,POOL)
box('Overflow shallow water',((px0+px1)/2,py0-.36,-.43),(px1-px0+.4,.33,.018),water,POOL,.002)
box('Pool foundation front fascia',((px0+px1)/2,py0-.51,-1.19),(px1-px0+.8,.18,1.53),concrete,POOL)

def ladder(name,x,y,z,side=-1):
    for dx in (-.30,.30):
        # Two curved stainless rails turn over the coping into the water.
        pts=[(x+dx,y+.44,z),(x+dx,y+.44,z+.48)]
        for i in range(13):
            a=pi-i*pi/12;pts.append((x+dx,y+.16+.28*cos(a),z+.48+.28*sin(a)))
        pts.extend([(x+dx,y-.12,z+.12),(x+dx,y-.12,z-.8)])
        pipe(name+' / curved rail',pts,.029,steel,POOL)
    for dz in (-.17,-.45,-.73):beam(name+' / submerged rung',(x-.30,y-.12,z+dz),(x+.30,y-.12,z+dz),.045,steel,POOL,.08)
ladder('Pool ladder',8.7,-6.85,.15)
# Raised octagonal hot tub on the eastern deck.
spa_poly=[(12.1,-2.35),(16.9,-2.35),(17.4,-2.85),(17.4,-5.75),(16.9,-6.25),(12.1,-6.25),(11.6,-5.75),(11.6,-2.85)]
prism('Jacuzzi cedar cabinet',list(reversed(spa_poly)),.03,.57,wood,POOL)
spa_inner=[(14.5+(x-14.5)*.89,-4.3+(y+4.3)*.86) for x,y in spa_poly]
prism('Jacuzzi tile basin',list(reversed(spa_inner)),.55,.62,tile,POOL)
prism('Jacuzzi water',list(reversed(spa_inner)),.62,.65,water,POOL,.012)
for a,b in zip(spa_poly,spa_poly[1:]+spa_poly[:1]):
    av=Vector((*a,.71));bv=Vector((*b,.71));c=(av+bv)/2;d=bv-av
    box('Jacuzzi coping',c,(d.length,.24,.18),tile,POOL,.03,math.atan2(d.y,d.x))
ladder('Jacuzzi ladder',12.4,-6.40,.67)
# Timber dining deck, with open gravel border and pale retaining parapet.
for i in range(40):
    y=-12.65+i*.151
    box('Dining terrace teak plank',(14.67,y,.085),(7.3,.14,.13),random.choice(deckwood),DECK,.008)
box('East boundary parapet',(18.65,-8.30,.46),(.25,9.70,.96),plaster)
box('Dining terrace front parapet',(14.8,-13.0,.46),(7.90,.25,.96),plaster)
box('Gravel bed east',(18.25,-8.45,.095),(.5,8.5,.12),stone_mats[4],DECK,.008)
for i in range(190):
    x=random.uniform(18.03,18.48);y=random.uniform(-12.65,-4.15)
    globe('Pebble',(x,y,.18),(.06,.045,.028),random.choice(stone_mats),DECK,1)
box('Gravel strip below overflow',(2.1,-13.85,-1.65),(18.4,.70,.15),stone_mats[1],DECK,.005)

def lounger(name,x,y,z,ang=0):
    def pos(a,b,c):return(x+a*cos(ang)-b*sin(ang),y+a*sin(ang)+b*cos(ang),z+c)
    for xx in (-.34,.34):
        for yy in (-.75,.75):beam(name+' / legs',pos(xx,yy,0),pos(xx,yy,.36),.055,wood,DECK)
        beam(name+' / chassis',pos(xx,-1,.33),pos(xx,1,.33),.06,wood,DECK)
    for i in range(12):box(name+' / teak seat slat',pos(0,-.88+i*.104,.38),(.78,.086,.06),deckwood[2],DECK,.007,ang)
    back=box(name+' / raised backrest',pos(0,.70,.65),(.77,.85,.055),deckwood[2],DECK,.018)
    back.rotation_euler=(.48,0,ang)
    cushion=box(name+' / linen cushion',pos(0,-.28,.46),(.69,1.3,.08),white,DECK,.04,ang)
    pillow=box(name+' / head pillow',pos(0,.80,.78),(.57,.30,.12),white,DECK,.055);pillow.rotation_euler=(.48,0,ang)
    for xx in (-.42,.42):
        wheel=cylinder(name+' / wheel',pos(xx,.74,.16),.115,.05,dark,DECK,16);wheel.rotation_euler[1]=pi/2
for i in range(3):lounger('Poolside chaise %d'%i,-3.7+i*1.6,-4.85,.07,pi)
for i in range(2):lounger('Lawn chaise %d'%i,-9.1+i*1.5,-8.4,.24,pi+.18)
lounger('Teak deck chaise',12.25,-9.6,.16,-.2)

def chair(name,x,y,z,ang=0):
    def pos(a,b,c):return(x+a*cos(ang)-b*sin(ang),y+a*sin(ang)+b*cos(ang),z+c)
    for a in (-.23,.23):
        for b in (-.24,.24):beam(name+' / leg',pos(a,b,0),pos(a*.9,b*.9,.49),.035,wood,DECK)
    box(name+' / seat',pos(0,0,.47),(.56,.57,.065),deckwood[2],DECK,.02,ang)
    for xx in (-.25,.25):beam(name+' / back upright',pos(xx,.24,.40),pos(xx,.31,1.02),.04,wood,DECK)
    for i in range(5):beam(name+' / back spindle',pos(-.18+i*.09,.27,.56),pos(-.18+i*.09,.30,.99),.035,deckwood[2],DECK)
    box(name+' / top rail',pos(0,.30,1.04),(.55,.055,.055),wood,DECK,.012,ang)

def parasol(name,x,y,z,r=1.60):
    cylinder(name+' / weighted base',(x,y,z+.04),.30,.08,concrete,DECK)
    cylinder(name+' / mast',(x,y,z+1.40),.035,2.8,steel,DECK)
    verts=[(x,y,z+3.05)];faces=[];segments=12
    # Ringed, gently scalloped canvas canopy, alternating triangular panels.
    for rr,zz in [(.20,2.92),(.52,2.77),(1,2.49)]:
        for i in range(segments):
            a=2*pi*i/segments;verts.append((x+r*rr*cos(a),y+r*rr*sin(a),z+zz))
    for i in range(segments):faces.append((0,1+i,1+(i+1)%segments))
    for k in range(2):
        for i in range(segments):
            a=1+k*segments+i;b=1+k*segments+(i+1)%segments
            faces.append((a,a+segments,b+segments,b))
    canopy=obj(name+' / tailored indigo canopy',verts,faces,blue,DECK);canopy.data.materials.append(blue2)
    for p in canopy.data.polygons:p.material_index=p.index%2
    so=canopy.modifiers.new('Canvas thickness','SOLIDIFY');so.thickness=.014
    for i in range(segments):
        a=2*pi*i/segments
        pipe(name+' / canopy seam',[(x,y,z+3.052),(x+r*.52*cos(a),y+r*.52*sin(a),z+2.776),(x+r*cos(a),y+r*sin(a),z+2.495)],.008,blue2,DECK)
    cylinder(name+' / finial',(x,y,z+3.1),.052,.12,steel,DECK)

def dining(name,x,y,z,r=.92):
    cylinder(name+' / pedestal',(x,y,z+.38),.10,.76,wood,DECK)
    for ang in (0,pi/2):box(name+' / foot',(x,y,z+.05),(1.03,.10,.10),wood,DECK,.015,ang)
    cylinder(name+' / circular tabletop',(x,y,z+.80),r,.09,deckwood[2],DECK,64)
    for a in (0,pi/2,pi,3*pi/2):chair(name+' / chair',x+1.37*cos(a),y+1.37*sin(a),z,a-pi/2)
    parasol(name+' / umbrella',x,y,z,1.65)
dining('East dining set',15.45,-10.55,.17)
dining('West garden dining set',-11.5,-10.55,.23,.79)
# Barbecue with lid, side shelves, wheeled cart and gas cylinder.
box('Barbecue cart',(16.6,-7.7,.75),(1.15,.64,.96),dark,DECK,.06)
box('Barbecue domed lid',(16.6,-7.7,1.34),(1.20,.69,.38),black,DECK,.17)
box('Barbecue lid pull',(16.6,-8.09,1.38),(.64,.07,.055),steel,DECK,.02)
for x in (15.80,17.40):box('Barbecue cedar side shelf',(x,-7.7,1.10),(.4,.67,.075),wood,DECK)
for x in (16.3,16.6,16.9):
    k=cylinder('BBQ chrome control',(x,-8.04,1.05),.05,.045,steel,DECK,16);k.rotation_euler[0]=pi/2
for x in (16.2,17.):
    w=cylinder('BBQ wheel',(x,-7.68,.28),.14,.07,black,DECK,20);w.rotation_euler[0]=pi/2
cylinder('BBQ propane bottle',(17.67,-7.68,.53),.21,.67,red,DECK)
cylinder('Gas bottle valve',(17.67,-7.68,.94),.07,.15,steel,DECK)
pipe('Gas supply hose',[(17.67,-7.68,.98),(17.8,-7.37,.7),(17.2,-7.36,.8)],.023,black,DECK)

print('Pool, garage and furniture complete',flush=True)

# Furnished rooms remain individually editable behind the floor-to-ceiling glass.
rug=noise_mat('Woven wool rug',(.37,.32,.25),(.57,.50,.39),35,bump=.025)
walnut=noise_mat('Interior walnut cabinetry',(.060,.025,.012),(.17,.085,.039),4,bump=.015,mapping=(5,5,.25))
def sofa(name,x,y,z,w=3.0,ang=0,mat=white):
    def pos(a,b,c):return (x+a*cos(ang)-b*sin(ang),y+a*sin(ang)+b*cos(ang),z+c)
    box(name+' / upholstered base',pos(0,0,.34),(w,.95,.40),mat,INTERIOR,.12,ang)
    box(name+' / back',pos(0,.43,.81),(w,.25,.88),mat,INTERIOR,.10,ang)
    for xx in (-w/2+.1,w/2-.1):box(name+' / arm',pos(xx,0,.66),(.24,1.0,.57),mat,INTERIOR,.10,ang)
    for i in range(3):
        xx=-w/2+.28+(i+.5)*(w-.56)/3
        box(name+' / loose seat cushion',pos(xx,-.05,.60),((w-.63)/3,.76,.18),mat,INTERIOR,.075,ang)
    for xx in (-w*.30,w*.30):
        o=box(name+' / accent pillow',pos(xx,.23,.96),(.48,.17,.44),red,INTERIOR,.10,ang)
        o.rotation_euler[1]=-.12 if xx<0 else .12
    for xx in (-w/2+.2,w/2-.2):
        for yy in (-.3,.3):box(name+' / foot',pos(xx,yy,.10),(.065,.065,.2),steel,INTERIOR,.01)

box('Living room wool rug',(4.5,2.8,3.758),(6.0,3.8,.032),rug,INTERIOR,.03)
sofa('Upper living sofa',4.4,4.2,3.76,3.8)
sofa('Upper lounge chair',7.25,2.9,3.76,1.25,pi/2,red)
box('Living coffee table',(4.4,2.45,4.18),(1.9,.87,.10),walnut,INTERIOR,.04)
for x in (3.62,5.18):box('Coffee table leg',(x,2.45,3.98),(.05,.70,.38),dark,INTERIOR,.01)
for i in range(3):box('Art books on coffee table',(4.5,2.42,4.26+i*.037),(.43,.33,.035),[white,red,dark][i],INTERIOR,.004,rot=.12*i)
cylinder('Ceramic coffee bowl',(3.90,2.43,4.27),.15,.09,white,INTERIOR)
box('Television low cabinet',(4.7,7.7,4.05),(4.4,.65,.56),walnut,INTERIOR,.05)
box('Living room television',(4.7,7.65,5.10),(2.55,.10,1.45),black,INTERIOR,.025)
box('Television screen',(4.7,7.58,5.1),(2.43,.015,1.32),dark,INTERIOR,.004)
beam('TV stand',(4.7,7.7,4.36),(4.7,7.7,4.55),.085,steel,INTERIOR)
# Kitchen at the uphill side of the open-plan upper floor.
for x in (-10.7,-9.5,-8.3,-7.1,-5.9,-4.7):
    box('Kitchen base cabinet',(x,7.55,4.19),(1.18,.85,.88),walnut,INTERIOR,.025)
    box('Kitchen drawer front',(x,7.10,4.35),(1.12,.04,.42),wood,INTERIOR,.009)
    box('Kitchen cabinet handle',(x,7.06,4.42),(.34,.033,.025),steel,INTERIOR,.005)
box('Kitchen stone countertop',(-7.7,7.5,4.70),(7.55,1.02,.12),plaster,INTERIOR,.024)
box('Kitchen dark splashback',(-7.7,8.06,5.1),(7.6,.05,.76),stone_mats[2],INTERIOR,.015)
box('Kitchen upper cupboards',(-8.4,7.83,5.96),(5.9,.50,1.02),white,INTERIOR,.02)
box('Kitchen island',(-6.8,4.8,4.18),(3.6,1.25,.86),walnut,INTERIOR,.03)
box('Kitchen island top',(-6.8,4.8,4.68),(3.85,1.45,.13),plaster,INTERIOR,.035)
box('Black induction hob',(-6.0,7.46,4.778),(1.0,.64,.03),black,INTERIOR,.015)
for x in (-6.23,-5.77):
    for y in (7.29,7.59):cylinder('Induction cooking ring',(x,y,4.799),.12,.006,steel,INTERIOR,32)
box('Refrigerator',(-2.55,7.54,5.03),(1.45,.95,2.55),steel,INTERIOR,.06)
box('Fridge center division',(-2.55,7.055,5.03),(.015,.015,2.5),black,INTERIOR,.002)
for x in (-2.7,-2.4):box('Fridge handle',(x,7.01,5.08),(.035,.06,.57),dark,INTERIOR,.01)
for x in (-7.9,-6.8,-5.7):
    cylinder('Island stool seat',(x,3.65,4.45),.27,.10,walnut,INTERIOR)
    cylinder('Island stool stem',(x,3.65,4.10),.045,.67,steel,INTERIOR)
    cylinder('Island stool base',(x,3.65,3.80),.24,.055,steel,INTERIOR)
box('West dining table',(-10.1,1.3,4.55),(2.6,1.12,.10),walnut,INTERIOR,.045)
for x in (-11.1,-9.1):
    for y in (.90,1.7):box('Dining table leg',(x,y,4.14),(.065,.065,.78),dark,INTERIOR,.01)
for x in (-10.9,-9.3):
    chair('Indoor dining chair',x,.38,3.78,pi)
    chair('Indoor dining chair',x,2.25,3.78,0)
# Downstairs bedroom, closet wall and a second lounge.
box('Bedroom rug',(-1.85,3.1,.07),(4.4,5.3,.06),rug,INTERIOR,.03)
box('Platform bed frame',(-1.8,3.10,.30),(2.5,3.3,.45),walnut,INTERIOR,.08)
box('Bedroom mattress',(-1.8,3.10,.60),(2.36,3.13,.29),white,INTERIOR,.16)
box('Bedroom headboard',(-1.8,4.78,1.12),(3.0,.16,1.9),walnut,INTERIOR,.06)
box('Linen bed cover',(-1.8,2.55,.79),(2.38,2.0,.12),white,INTERIOR,.10)
box('Warm woven bed runner',(-1.8,1.73,.865),(2.40,.66,.035),red,INTERIOR,.015)
for x in (-2.42,-1.18):box('Bedroom pillow',(x,4.08,.86),(.90,.61,.18),white,INTERIOR,.13)
for x in (-3.70,.1):
    box('Bedside nightstand',(x,4.22,.44),(.73,.60,.8),walnut,INTERIOR,.03)
    cylinder('Bedside lamp base',(x,4.22,.90),.13,.07,steel,INTERIOR)
    cylinder('Bedside lamp stem',(x,4.22,1.06),.026,.3,steel,INTERIOR)
    cylinder('Bedside linen lampshade',(x,4.22,1.33),.24,.38,white,INTERIOR,32,.19)
box('Walk-in wardrobe backing',(-7.9,7.9,1.50),(7.2,.35,2.9),walnut,INTERIOR,.03)
for x in (-10.5,-8.7,-6.9,-5.1):
    box('Wardrobe vertical panel',(x,7.30,1.51),(.06,1.3,2.9),wood,INTERIOR,.009)
for z in (.25,1.65,2.87):box('Wardrobe shelving',(-7.8,7.3,z),(7.2,1.3,.07),wood,INTERIOR,.008)
sofa('Lower media sofa',5.4,3.8,.08,3.2)
box('Lower media rug',(5.4,2.1,.09),(4.5,3.0,.04),rug,INTERIOR)
box('Lower lounge table',(5.4,1.9,.45),(1.55,.80,.09),walnut,INTERIOR,.04)
for x in (4.9,5.9):box('Lower table foot',(x,1.9,.27),(.06,.64,.35),dark,INTERIOR,.01)
# A recognisable telescope on the long glass balcony.
for a in (0,2*pi/3,4*pi/3):beam('Telescope tripod',(5.8+.47*cos(a),-1.5+.47*sin(a),3.69),(5.8,-1.5,4.83),.036,steel,DETAIL)
beam('Telescope barrel',(5.8,-1.5,4.84),(5.8,-2.21,5.11),.15,white,DETAIL)
beam('Telescope lens hood',(5.8,-2.17,5.10),(5.8,-2.38,5.18),.20,dark,DETAIL)

# Planting: mesh leaves and tapered fronds, without external textures.
def leaf_cloud(name,center,size,count=600,conical=False):
    vs=[];fs=[]
    cx,cy,cz=center;sx,sy,sz=size
    for i in range(count):
        if conical:
            h=random.random();ang=random.random()*2*pi;r=(1-h)**.65*random.random()**.4
            x=cx+sx*r*cos(ang);y=cy+sy*r*sin(ang);z=cz+sz*h
        else:
            v=Vector((random.gauss(0,1),random.gauss(0,1),random.gauss(0,1))).normalized();r=random.random()**.20
            x=cx+v.x*sx*r;y=cy+v.y*sy*r;z=cz+v.z*sz*r
        length=random.uniform(.085,.19);width=length*.46
        d=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-.4,1))).normalized()*length
        q=d.cross(Vector((0,0,1))).normalized()*width;p=Vector((x,y,z));a=len(vs)
        vs.extend([tuple(p-d),tuple(p+q),tuple(p+d),tuple(p-q),tuple(p+Vector((0,0,.025)))])
        fs.extend([(a,a+1,a+4),(a+1,a+2,a+4),(a+2,a+3,a+4),(a+3,a,a+4)])
    o=obj(name,vs,fs,None,GARDEN)
    for m in leaves:o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=random.choices(range(5),[3,4,2,3,1])[0]
    return o

def pot(name,x,y,z,r=.32,h=.57):
    cylinder(name+' / ceramic planter',(x,y,z+h/2),r*.82,h,plaster,GARDEN,40,r)
    cylinder(name+' / rolled rim',(x,y,z+h-.035),r*1.07,.095,plaster,GARDEN,40)
    cylinder(name+' / soil',(x,y,z+h+.015),r*.90,.032,soil,GARDEN)
    return z+h
def cypress(name,x,y,z,h=2.7,r=.47,planter=True):
    if planter:z=pot(name,x,y,z,.35,.61)
    cylinder(name+' / trunk',(x,y,z+h*.44),.047,h*.86,bark,GARDEN,12)
    for i in range(8):
        t=(i+.5)/9;radius=r*(1-t)**.62*.80
        globe(name+' / dense foliage core',(x+.025*sin(i*2),y,z+h*(.12+t*.83)),(radius,radius,h*.145),leaves[i%4],GARDEN,2)
    leaf_cloud(name+' / needle foliage',(x,y,z+.15),(r,r,h-.12),1500,True)
def topiary(name,x,y,z,r=.46):
    z=pot(name,x,y,z,.32,.56)
    cylinder(name+' / stem',(x,y,z+.34),.035,.68,bark,GARDEN,12)
    leaf_cloud(name+' / clipped crown',(x,y,z+.85),(r,r,r*1.03),850)
for x,y,z,h in [(-13.2,-12.2,.24,2.5),(-7.2,-11.9,.24,2.1),(11.15,-12.3,.17,2.4),(18.0,-12.1,.17,2.6),(18.1,-5.9,.16,2.5),(-13.4,-3.1,3.67,2.15),(19,2.8,3.60,2.0)]:
    cypress('Potted Italian cypress',x,y,z,h,.34)
for x,y,z in [(-12.1,-6.0,.23),(-7.2,-6.3,.23),(-12.4,-11.5,.23),(-8.2,-2.0,.12),(7.4,-2.0,3.65)]:topiary('Ball topiary',x,y,z)
for x in (8.2,11.75):cypress('Entrance planter',x,10.65,3.79,1.8,.32)

def palm(name,x,y,z,h=10):
    verts=[];faces=[];rings=21;sides=12
    def center(t):return Vector((x+.42*t*t,y+.25*sin(t*pi/2),z+h*t))
    for j in range(rings):
        t=j/(rings-1);c=center(t);r=.20*(1-.45*t)
        for i in range(sides):
            a=i*2*pi/sides;verts.append(tuple(c+Vector((r*cos(a),r*sin(a),0))))
    for j in range(rings-1):
        for i in range(sides):a=j*sides+i;b=j*sides+(i+1)%sides;faces.append((a,b,b+sides,a+sides))
    obj(name+' / curved trunk',verts,faces,bark,GARDEN)
    for j in range(36):
        t=j/36;c=center(t);cylinder(name+' / trunk ring',c,.207*(1-.45*t),.040,bark,GARDEN,12)
    crown=center(1);vs=[];fs=[]
    for j in range(15):
        ang=j*2.399963;L=random.uniform(2.8,4.3);d=Vector((cos(ang),sin(ang),0));s=Vector((-sin(ang),cos(ang),0))
        rise=random.uniform(.4,1.9)
        def spine(t):return crown+d*(t*L)+Vector((0,0,rise*sin(t*pi*.8)-1.9*t*t))
        pipe(name+' / arching frond stem',[tuple(spine(t/14)) for t in range(15)],.018,leaves[1],GARDEN)
        for k in range(1,29):
            t=k/30;p=spine(t);width=.63*sin(pi*t)**.7
            for sign in (-1,1):
                end=p+s*(width*sign)+d*.30+Vector((0,0,-.14-.13*t));a=len(vs)
                vs.extend([tuple(p-d*.05),tuple(p+d*.09),tuple((p+end)*.5+d*.04+Vector((0,0,.035))),tuple(end)])
                fs.extend([(a,a+1,a+2),(a,a+2,a+3)])
    o=obj(name+' / feathered palm canopy',vs,fs,leaves[0],GARDEN);o.data.materials.append(leaves[2])
    for p in o.data.polygons:p.material_index=int(random.random()<.22)

for x,y,h in [(-18,-1,10.8),(-21,5,12.6),(24,5,11.7),(-26,17,10.5),(26,25,13)]:palm('California fan palm',x,y,terrain_z(x,y),h)
# Soft shrub banks frame the terrace and blend its foundation into the hillside.
for i in range(28):
    x=-18.2+random.uniform(-1.6,1.6);y=-15+i*.94;z=terrain_z(x,y)
    leaf_cloud('Western boundary hedge',(x,y,z+.78),(random.uniform(.7,1.2),.85,.85),350)
for i in range(28):
    x=22+random.uniform(-1.2,1.2);y=-15+i*.9;z=terrain_z(x,y)
    leaf_cloud('Eastern boundary shrubs',(x,y,z+.63),(.90,.90,.75),330)
for i in range(17):
    x=-15+i*2;y=-16-random.uniform(0,2.4);z=terrain_z(x,y)
    leaf_cloud('Pool slope planting',(x,y,z+.45),(.95,.8,.60),380)
for x,y,h in [(-29,27,7),(-21,31,8.2),(0,29,7.8),(11,31,9.4),(24,31,7.4),(35,17,8.2),(-34,13,6.3)]:
    cypress('Hillside cypress',x,y,terrain_z(x,y),h,1.1,False)
for i in range(55):
    x=random.uniform(-39,39);y=random.uniform(22,43);z=terrain_z(x,y)
    leaf_cloud('Distant hillside scrub',(x,y,z+.45),(.95,.85,.65),160)
# Climbing ivy on the roadside wall, with visible stems.
for x0 in (-11.6,-7.1,-2.5,6.7):
    pts=[]
    for k in range(14):pts.append((x0+.22*sin(k*.8),9.63,3.9+k*.185))
    pipe('Climbing ivy stem',pts,.013,bark,GARDEN)
    for k in range(7):
        x=x0+random.uniform(-.72,.72);z=4.1+k*.36
        leaf_cloud('Ivy leaves on street elevation',(x,9.68,z),(.68,.11,.43),130)

def agave(name,x,y,z,r=.70):
    vs=[];fs=[]
    for i in range(18):
        a=i*2.4;L=random.uniform(.65,1.3)*r;d=Vector((cos(a),sin(a),0));s=Vector((-sin(a),cos(a),0));p=Vector((x,y,z));b=len(vs)
        mid=p+d*L*.45+Vector((0,0,L*.46));end=p+d*L+Vector((0,0,L*.40))
        vs.extend([tuple(p),tuple(mid+s*L*.11),tuple(mid+Vector((0,0,.05))),tuple(mid-s*L*.11),tuple(end)])
        fs.extend([(b,b+1,b+2),(b,b+2,b+3),(b+1,b+4,b+2),(b+2,b+4,b+3)])
    return obj(name,vs,fs,leaves[2],GARDEN)
for x,y in [(-15.8,-12),(-16.2,-5),(20.8,-9),(20.6,-3),(-18,8),(23,9)]:agave('Agave on hillside',x,y,terrain_z(x,y),1.2)

# Bins, wall lanterns, downlights and restrained warm interiors.
binblue=material('Blue recycling bin',(.027,.10,.30),.50)
bingreen=material('Green refuse bin',(.034,.10,.055),.55)
for x,mat in [(6.5,binblue),(7.20,bingreen)]:
    box('Street refuse bin',(x,10.05,4.26),(.58,.67,.95),mat,DETAIL,.07)
    box('Refuse bin lid',(x,10.05,4.77),(.64,.74,.10),mat,DETAIL,.035)
    box('Refuse bin handle',(x,9.73,4.70),(.34,.08,.06),black,DETAIL,.015)
    for xx in (x-.25,x+.25):
        o=cylinder('Bin wheel',(xx,9.81,3.89),.11,.045,black,DETAIL,16);o.rotation_euler[1]=pi/2
emission=material('Warm lamp diffuser',(.95,.61,.27),.40)
ep=emission.node_tree.nodes.get('Principled BSDF');ep.inputs['Emission Color'].default_value=(1,.66,.34,1);ep.inputs['Emission Strength'].default_value=3
def area(name,loc,power,color,size,target):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);LIGHT.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
for x in (-10,-3,4,8):
    cylinder('Upper soffit recessed trim',(x,-.70,6.90),.10,.025,dark,DETAIL)
    cylinder('Upper soffit warm downlight',(x,-.70,6.88),.073,.018,emission,DETAIL)
    cylinder('Lower soffit recessed trim',(x,-1.6,3.30),.10,.03,dark,DETAIL)
    cylinder('Lower soffit diffuser',(x,-1.6,3.28),.072,.02,emission,DETAIL)
for x,y,z in [(-8,4.5,6.68),(4.5,4.0,6.70),(-1.7,3.0,3.13),(5.5,3,3.13)]:area('Interior warm ceiling light',(x,y,z),170,(1,.77,.53),3,(x,y,0))
for x in (10.7,16):
    box('Entry wall light housing',(x,11.52,6.25),(.16,.16,.32),dark,DETAIL,.025)
    box('Entry wall light diffuser',(x,11.61,6.25),(.105,.025,.22),emission,DETAIL,.01)
for x in (-7.9,-6.8,-5.7):
    cylinder('Kitchen pendant cable',(x,4.8,6.44),.009,.93,black,INTERIOR,10)
    cylinder('Kitchen pendant shade',(x,4.8,5.91),.22,.18,dark,INTERIOR,32,.09)
    cylinder('Kitchen pendant glow',(x,4.8,5.81),.185,.02,emission,INTERIOR,32)

print('Interiors and landscape complete',flush=True)

# Clear daylight, with an architectural-photography camera set.
world=bpy.data.worlds.new('Vinewood · late afternoon sky');scene.world=world;world.use_nodes=True
nodes=world.node_tree.nodes;links=world.node_tree.links;nodes.clear()
out=nodes.new('ShaderNodeOutputWorld');bg=nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.16
sky=nodes.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=math.radians(31);sky.sun_rotation=math.radians(230);sky.air_density=1.1;sky.aerosol_density=1.4;sky.sun_disc=False
links.new(sky.outputs['Color'],bg.inputs['Color']);links.new(bg.outputs['Background'],out.inputs['Surface'])
sun_data=bpy.data.lights.new('Sun · warm southwest','SUN');sun_data.energy=2.4;sun_data.angle=math.radians(4);sun_data.color=(1,.86,.67)
sun=bpy.data.objects.new('Sun · warm southwest',sun_data);LIGHT.objects.link(sun);sun.rotation_euler=(math.radians(29),math.radians(-24),math.radians(-28))
area('Sky fill',(1,-15,19),1400,(.73,.84,1),22,(1,0,2))
def camera(name,loc,target,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);CAMS.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=400
    d.passepartout_alpha=1;return o
hero=camera('01 · Pool elevation / HERO',(28,-47,18),(1.8,-.6,2.3),43)
poolcam=camera('02 · Pool terrace / eye level',(22,-25,9),(1,-1.8,2.9),34)
streetcam=camera('03 · Whispymound Drive / entrance',(24,23,10),(3.0,8.0,4.5),33)
aerial=camera('04 · Site overview',(-31,-39,34),(1.5,0,1.5),40)
scene.camera=hero
for frame,cam in [(1,hero),(2,poolcam),(3,streetcam),(4,aerial)]:
    marker=scene.timeline_markers.new(cam.name,frame=frame);marker.camera=cam
scene.frame_start=1;scene.frame_end=4;scene.frame_set(1)
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.cycles.max_bounces=8
scene.cycles.transmission_bounces=6
scene.cycles.transparent_max_bounces=6
scene.cycles.adaptive_threshold=.055
# Metal is supported by the installed Apple Silicon Blender build.
try:
    pref=bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type='METAL';pref.get_devices()
    for device in pref.devices:device.use=(device.type=='METAL')
    if any(d.type=='METAL' for d in pref.devices):scene.cycles.device='GPU'
except Exception as exc:print('CPU render fallback:',exc)
scene.render.resolution_x=1600;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.10
scene.render.filepath=os.path.join(ROOT,'renders','01_pool_hero.png')
scene.render.image_settings.color_depth='8'
scene['project']='Franklin Clinton · 3671 Whispymound Drive'
scene['description']='Reference-based architectural reconstruction of the GTA V Vinewood Hills safehouse. Approximate dimensions; exterior plus furnished visible rooms. All geometry and procedural materials authored in Blender.'
scene['reference_url']='https://www.gtabase.com/grand-theft-auto-v/properties/story-mode/3671-whispymound-drive-franklin-house'
scene['camera_guide']='Timeline frames 1–4 select Hero / Pool terrace / Street entrance / Aerial cameras.'
scene['units']='Meters; swimming pool width approximately 17.1 m; main roof height 7.4 m.'
readme=bpy.data.texts.new('START HERE · Project notes')
readme.write('FRANKLIN / 3671 WHISPYMOUND DRIVE\n\nReference-based GTA V villa study, modelled from publicly available screenshots.\nApproximate dimensions, not extracted game assets.\n\n11 labelled collections keep the building editable.\nAll materials are procedural; there are no missing texture dependencies.\nMetric units. Z=0 is the pool terrace; street and upper floor are Z=3.7m.\n\nCAMERAS\nTimeline frames 1/2/3/4 switch between Hero, Pool, Entrance and Aerial.\nNumpad 0 enters camera view. Home frames the complete scene.\n\nThe facade, pool, garage, furnishings and landscaping are separate objects.\nRoof objects can be hidden to inspect the furnished rooms.\n\nREBUILD\nRun scripts/build_franklin.py with Blender in background mode.\n')
# Store an immediately useful solid/material-color viewport on opening the file.
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            sp=ar.spaces.active;sp.clip_end=400;sp.shading.type='MATERIAL'
            sp.shading.use_scene_world=False;sp.shading.studiolight_rotate_z=.5
            sp.region_3d.view_perspective='CAMERA';sp.overlay.show_overlays=False
        elif ar.type=='PROPERTIES':ar.spaces.active.context='RENDER'
bpy.ops.object.select_all(action='DESELECT')
scene.camera=hero
os.makedirs(os.path.join(ROOT,'renders'),exist_ok=True)
blend_path=os.path.join(ROOT,'Franklin_3671_Whispymound.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
stats={'objects':len(scene.objects),'meshes':len(bpy.data.meshes),'materials':len(bpy.data.materials),'collections':len(collections),'cameras':4,'blend_file':blend_path,'render_engine':scene.render.engine,'device':scene.cycles.device,'vertices':sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH')}
with open(os.path.join(ROOT,'scene_manifest.json'),'w') as f:json.dump(stats,f,indent=2)
print('SAVED:',json.dumps(stats),flush=True)
if '--render' in sys.argv:
    if '--draft' in sys.argv:
        scene.render.resolution_percentage=55;scene.cycles.samples=16
        scene.render.filepath=os.path.join(ROOT,'renders','draft.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER COMPLETE',flush=True)
