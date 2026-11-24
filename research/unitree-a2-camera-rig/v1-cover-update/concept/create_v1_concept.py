from pathlib import Path
import html, math
P=Path(__file__).resolve().parent
s=[]
ink='#233348';muted='#5C6D7F';oem='#617487';teal='#087F8C';blue='#DDEFF2';purple='#7554A4';pale='#EDE7F5';amber='#A96F16';cream='#FFF3DB';metal='#52667A'
def add(x):s.append(x)
def rect(x,y,w,h,fill,stroke='none',sw=1,rx=0,dash=None):add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def path(d,fill='none',stroke=ink,sw=2,dash=None):add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def circle(x,y,r,fill,stroke='none',sw=1,dash=None):add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def text(x,y,t,size=23,color=ink,weight='normal',anchor='start',rotate=None):add(f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}"'+(f' transform="rotate({rotate} {x} {y})"' if rotate else '')+'>'+html.escape(t)+'</text>')
def lines(x,y,ts,size=23,color=muted,gap=29,weight='normal'):
 for i,t in enumerate(ts):text(x,y+i*gap,t,size,color,weight)
def arrow(x1,y1,x2,y2,color=muted):
 a=math.atan2(y2-y1,x2-x1);b=(x2-13*math.cos(a),y2-13*math.sin(a));pts=f'{x2},{y2} {b[0]-5*math.sin(a)},{b[1]+5*math.cos(a)} {b[0]+5*math.sin(a)},{b[1]-5*math.cos(a)}';add(f'<polygon points="{pts}" fill="{color}"/>')
def line(x1,y1,x2,y2,color=muted,sw=2,dash=None,head=False):
 add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
 if head:arrow(x1,y1,x2,y2,color)
def dim_h(x1,x2,y,label,color=oem):
 line(x1,y,x2,y,color,1.7);arrow(x2,y,x1,y,color);arrow(x1,y,x2,y,color);text((x1+x2)/2,y-11,label,22,color,'bold','middle')
def dim_v(y1,y2,x,label,color=oem):
 line(x,y1,x,y2,color,1.7);arrow(x,y2,x,y1,color);arrow(x,y1,x,y2,color);text(x-12,(y1+y2)/2,label,22,color,'bold','middle',-90)
def badge(x,y,label,color=teal):circle(x,y,20,color);text(x,y+8,label,24,'white','bold','middle')
add('<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1570" viewBox="0 0 1800 1570">')
rect(0,0,1800,1570,'#F2F5F7')
text(44,61,'A2 / V1 COVER CAMERA PLATFORM',42,ink,'bold')
text(44,104,'OEM V1 silhouette · commercial Sony quick release · underside pole bolt',27,muted)
text(44,144,'Concept revision 03   /   23 November 2026',21,muted)
rect(1430,28,326,62,cream,'#E1C38E',1,13)
text(1593,68,'CONCEPT ONLY',25,amber,'bold','middle')
text(1756,137,'2D DESIGN STUDY · NOT TO SCALE',20,muted,'bold','end')
# top view panel
rect(44,175,1058,875,'white','#DCE4EA',1.5,20)
text(76,220,'01   V1 OUTLINE + PROPOSED MOUNT LOCATIONS',25,ink,'bold')
text(76,255,'Outline reference from OEM drawing; new features shown in color.',22,muted)
# Drawing projection source coordinates; no parametric CAD claim.
# Actual OEM outline raster is x257..1109, y158..814. Ear locations and curves traced visually.
add('<g transform="translate(-18 210) scale(.9)">')
path('M257 327 Q257 292 294 277 Q319 266 328 238 L343 177 Q346 158 364 158 L397 158 Q414 158 419 180 L434 242 Q440 261 460 261 L875 261 Q898 261 903 242 L920 179 Q925 158 943 158 L975 158 Q992 158 997 179 L1012 241 Q1020 266 1042 277 L1081 297 Q1109 307 1109 341 L1109 647 Q1109 678 1082 691 L1042 711 Q1018 723 1010 749 L995 796 Q991 814 972 814 L942 814 Q924 814 919 797 L903 739 Q897 712 875 712 L461 712 Q440 712 434 737 L418 796 Q413 814 395 814 L363 814 Q346 814 342 796 L328 750 Q320 721 297 710 L280 701 Q257 692 257 665 Z','#F0F3F5',oem,3)
# reference inner deck shape, no copied enclosure cover screw pattern
path('M280 336 Q280 314 300 304 L331 288 L1006 288 L1079 319 Q1091 325 1091 345 L1091 642 Q1091 661 1074 672 L1008 695 L325 695 L292 682 Q278 676 278 657 Z','white','#B2BEC9',2)
# chassis attachment symbols at documented outer pitch, no hole-size claim
for x in [379,958]:
 for y in [184,788]:
  circle(x,y,10,'white',oem,2.5)
  circle(x,y,29,'none',amber,1.6,'6 5')
add('</g>')
# overall dimensions from OEM
for x in [213.3,980.1]:line(x,283,x,350,oem,1)
dim_h(213.3,980.1,298,'301 mm overall / OEM')
for x in [323.1,844.2]:line(x,326,x,370,oem,1)
dim_h(323.1,844.2,338,'204 mm attachment pitch')
for y in [352.2,942.6]:line(166,y,211,y,oem,1)
dim_v(352.2,942.6,174,'231 mm overall / OEM')
for y in [375.6,919.2]:line(981,y,1025,y,oem,1)
dim_v(375.6,919.2,1018,'213 mm attachment pitch')
# centerline and front arrow
line(234,650,962,650,'#B8C5CF',1.8,'9 7')
line(336,396,239,396,muted,2.5,head=True);text(242,425,'FRONT / LENS',18,muted,'bold')
# Sony illustrative ghost envelope, QR component correctly relative size (rounded)
rect(401,548,170,249,'none','#B7A7CC',2,15,'7 7')
rect(276,591,125,118,'none','#B7A7CC',2,10,'7 7')
# optional adapter register below metal QR
rect(402,591,155,118,blue,teal,2,8)
# nominal whole F38 kit footprint:53.4x38, shown at diagram scale 2.545 px/mm
rect(412,601,136,97,pale,purple,3,8)
rect(425,614,110,72,'#DAD0EA',purple,2,5)
# quick release button and lens arrow
rect(398,627,15,37,purple,purple,1,3)
line(487,650,441,650,purple,3,head=True)
text(480,638,'F38',20,purple,'bold','middle')
# finger access envelope near button on lens-facing side
path('M393 615 L366 615 L366 679 L393 679',fill='none',stroke=purple,sw=2,dash='5 5')
# annotations
badge(295,502,'A',purple)
lines(325,494,['Sony ZV-E1 + lens','Ghost envelope; exact lens TBD'],21,purple,28)
path('M477 532 L477 548',stroke=purple,sw=2)
text(278,824,'Proposed Falcam F38B3404',22,purple,'bold')
path('M479 799 L479 709',stroke=purple,sw=2)
# pole boss plan view rear centerline
circle(795,650,58,blue,teal,3)
circle(795,650,36,'none',teal,1.6,'5 5')
circle(795,650,9,'white',teal,2)
line(780,650,810,650,teal,1);line(795,635,795,665,teal,1)
badge(692,514,'B')
lines(723,507,['Stick behind Sony','Near centerline','Position provisional'],21,teal,28)
path('M795 575 L795 589',stroke=teal,sw=2)
lines(674,766,['Ø7 smooth clearance','Provisional design dimension'],21,teal,28)
path('M794 737 L794 712',stroke=teal,sw=2)
# card bottom notes
text(76,987,'4 attachment ears: keep bolt-head and tool access clear.',21,amber,'bold')
text(76,1021,'Use OEM nominal dimensions; check simplified STEP and physical rail fit.',20,muted)
# right cutaway panel
rect(1126,175,630,875,'white','#DCE4EA',1.5,20)
text(1158,220,'02   POLE FASTENER SECTION',25,ink,'bold')
text(1158,255,'Metal bolt inserts upward from UNDER the cover.',21,muted)
# fastener detail explanatory labels
lines(1158,312,['1/4-20 female thread + usable depth: VERIFY','Choose bolt length only after the stack is measured.'],20,amber,28,'bold')
# Stick body (section) x1406..1506 with interior
rect(1408,394,102,236,'#EBEFF3',metal,3,6)
# visible end tube break
path('M1407 393 L1432 383 L1458 403 L1484 383 L1511 394',stroke=metal,sw=3)
# inner hollow column / female insert block
rect(1422,408,74,169,'white',metal,1,0)
rect(1432,577,55,53,'#B7C5D0',metal,2,1)
rect(1451,586,17,44,'white',metal,1)
# thread symbolic hatch on female insert (not numerical detail)
for yy in range(591,625,7):
 line(1444,yy,1451,yy+4,metal,1.5);line(1468,yy+4,1475,yy,metal,1.5)
# print cover and reinforced boss section in teal
# broad cover ends at card safe edges
path('M1198 654 L1372 654 L1372 634 L1449 634 L1449 723 L1372 723 L1372 703 L1198 703 Z',blue,teal,3)
path('M1470 634 L1546 634 L1546 654 L1700 654 L1700 703 L1546 703 L1546 723 L1470 723 Z',blue,teal,3)
# hatching print material (simple diagonal dashes)
for xx in range(1213,1355,23):line(xx,696,xx+20,661,'#8FC5CF',1.7)
for xx in range(1560,1675,23):line(xx,696,xx+20,661,'#8FC5CF',1.7)
# ribs reinforce boss underside
path('M1285 703 L1372 751 L1372 703 Z',blue,teal,2)
path('M1546 703 L1633 751 L1546 751 Z',blue,teal,2)
# optional shallow locating seat walls
rect(1398,623,10,12,blue,teal,2,1)
rect(1510,623,10,12,blue,teal,2,1)
# broad washer/load spreader; split by shaft in section
rect(1371,724,178,13,'#9AAEBE',metal,2,1)
# bolt shank and threaded insertion
rect(1453,598,13,157,'#8DA0B0',metal,2,0)
for yy in range(603,630,6):line(1453,yy,1466,yy-4,metal,1.5)
# bolt head
rect(1431,738,57,27,'#7E94A7',metal,2,4)
rect(1448,749,23,8,'#304456','#304456',1,1)
# arrow up from under cover
line(1460,827,1460,777,teal,3,head=True)
text(1460,859,'INSERT FROM UNDERNEATH',20,teal,'bold','middle')
# detail labels with leader lines
lines(1158,423,['Fixed lower','stick end'],21,metal,27,'bold')
path('M1290 431 L1360 431 L1407 458',stroke=metal,sw=2)
lines(1158,522,['Optional shallow','locating seat','Outside diameter TBD'],20,teal,26)
path('M1348 550 L1379 550 L1402 622',stroke=teal,sw=2)
lines(1552,421,['Smooth hole','through print'],20,teal,26,'bold')
path('M1576 458 L1555 483 L1484 645 L1472 645',stroke=teal,sw=2)
lines(1158,781,['Reinforced boss','+ printed ribs'],20,teal,27,'bold')
path('M1334 777 L1352 746',stroke=teal,sw=2)
lines(1552,792,['Broad metal washer','or load spreader'],20,metal,27,'bold')
path('M1553 765 L1532 737',stroke=metal,sw=2)
lines(1158,911,['1/4-20 metal bolt → washer → printed boss → stick','Exact grip, engagement and underside clearance TBD.'],20,muted,29)
text(1158,1006,'Section is schematic; material thickness is not specified.',20,muted)
# Footer 3 columns with clearer outcomes
rect(44,1074,1712,434,'#E8F0F3','#D4E0E6',1.5,20)
text(76,1121,'REFERENCE GEOMETRY + NEXT DESIGN DECISIONS',26,ink,'bold')
line(590,1150,590,1464,'#C8D7E0',2);line(1164,1150,1164,1464,'#C8D7E0',2)
text(77,1178,'OEM V1 REFERENCE',22,oem,'bold')
lines(77,1220,['OEM enclosure supplies the shape reference.','301 × 231 mm overall outline','204 × 213 mm outer attachment pitch','Simplified STEP differs slightly: verify rail fit.'],21,ink,34)
text(77,1385,'H2S: 340 × 320 × 340 mm',23,teal,'bold')
lines(77,1420,['The 301 × 231 mm envelope fits the XY bed.','Allow for a brim and the final printing orientation.'],20,muted,29)
text(618,1178,'SONY QUICK RELEASE',22,purple,'bold')
lines(618,1220,['Proposed F38B3404: 53.4 × 38 × 20.8 mm','Base stays on cover; plate stays on Sony.','Kit: 51.7 g; lens arrow/button faces the lens.','Keep finger access; measure the bolt centers.'],21,ink,34)
lines(618,1385,['Optional small adapter pad with a perimeter','anti-rotation register; do not infer bolt holes','from a product photograph.'],21,muted,31)
text(1192,1178,'FIT & ACCESS CHECKS',22,teal,'bold')
lines(1192,1220,['Verify the stick’s female thread and depth.','Confirm chassis clearance below the bolt head.','Preserve both batteries’ side extraction.','Keep legs, perception and ventilation clear.'],21,ink,34)
lines(1192,1385,['Pole working height and lever loads remain TBD.','Validate the printed boss, fasteners and retention','before moving with the cameras installed.'],20,muted,31)
text(44,1546,'GRAY = OEM REFERENCE    /    TEAL = PROPOSED PRINTED FEATURES    /    PURPLE = COMMERCIAL QUICK RELEASE',18,muted,'bold')
text(1756,1546,'ADAPTER NOT MODELED',18,muted,'bold','end')
add('</svg>')
(P/'a2-v1-cover-concept.svg').write_text('\n'.join(s))
print(P/'a2-v1-cover-concept.svg')
