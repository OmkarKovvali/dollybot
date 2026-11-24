from pathlib import Path
import html, math
P=Path(__file__).resolve().parent
W,H=1800,1580
s=[]
def add(x):s.append(x)
def rect(x,y,w,h,fill,stroke='none',sw=1,rx=0,dash=None):add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def arrow_head(x1,y1,x2,y2,color='#526376'):
 a=math.atan2(y2-y1,x2-x1); length=13; radius=5
 bx=x2-length*math.cos(a);by=y2-length*math.sin(a)
 pts=f'{x2},{y2} {bx-radius*math.sin(a)},{by+radius*math.cos(a)} {bx+radius*math.sin(a)},{by-radius*math.cos(a)}'
 add(f'<polygon points="{pts}" fill="{color}"/>')
def line(x1,y1,x2,y2,stroke='#223347',sw=2,dash=None,marker=None):
 add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
 if marker:arrow_head(x1,y1,x2,y2,stroke)

def path(d,fill='none',stroke='#223347',sw=2,dash=None):add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def circle(x,y,r,fill,stroke='none',sw=1):add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def text(x,y,t,size=24,fill='#223347',weight='normal',anchor='start'):
 add(f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{html.escape(t)}</text>')
def lines(x,y,items,size=23,fill='#526376',gap=30,weight='normal'):
 for i,t in enumerate(items):text(x,y+i*gap,t,size,fill,weight)
def badge(x,y,t,color='#087F8C'):
 circle(x,y,19,color);text(x,y+8,t,22,'white','bold','middle')
ink='#223347';muted='#526376';teal='#087F8C';blue='#D8EDF2';metal='#53677B';purple='#7755A5';palePurple='#EBE4F4';amber='#B47A1D';paleAmber='#FFF2D9';body='#E4E9EE'
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add('''<defs>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#526376"/></marker>
<marker id="tealArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#087F8C"/></marker>
<pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(30)"><line x1="0" y1="0" x2="0" y2="10" stroke="#E5B86D" stroke-width="3"/></pattern>
</defs>''')
rect(0,0,W,H,'#F3F5F7')
text(44,62,'A2 / DUAL-CAMERA RIG',44,ink,'bold')
text(44,104,'Rail-mounted concept for Sony ZV-E1 + Insta360 X6',28,muted)
text(44,144,'Bare factory rails   •   Bambu Lab H2S   •   23 November 2026',22,muted)
rect(1385,30,370,62,paleAmber,'#E4C893',1,14)
text(1570,70,'CONCEPT ONLY · 02',25,amber,'bold','middle')
text(1755,131,'NOT TO SCALE · NO 3D CAD',21,muted,'bold','end')
# SIDE VIEW CARD
rect(44,178,1088,700,'white','#DDE4EA',1.5,20)
text(76,223,'01   SIDE VIEW',27,ink,'bold')
text(76,256,'Low camera, supported pole, clear battery access',23,muted)
# Front orientation
line(265,305,150,305,muted,3,marker='arrow');text(170,288,'FRONT',20,muted,'bold')
# Robot body silhouette (schematic)
path('M142 596 L215 571 L350 588 L420 609 L832 609 L927 579 L1014 593 L1045 626 L1028 681 L924 690 L865 715 L366 715 L302 688 L170 682 Z',body,'#98A7B5',3)
# battery access side face
rect(403,626,434,78,'#F7F8FA','#A3B1BD',2,9)
line(619,627,619,703,'#BBC6CF',2)
text(620,675,'SIDE-SLIDING BATTERIES',20,muted,'bold','middle')
# legs illustrative
for x,sign in [(318,1),(900,-1)]:
 circle(x,686,30,'#CDD7DF','#9AA9B8',3)
 path(f'M{x} 711 L{x+sign*72} 765 L{x+sign*18} 822','none','#A8B7C4',22)
 path(f'M{x} 711 L{x+sign*72} 765 L{x+sign*18} 822','none','#62788C',3)
 line(x+sign*18-25,826,x+sign*18+30,826,metal,9)
# native perception keepouts
for x,y in [(167,619),(1021,621)]:
 circle(x,y,23,'#F4DAA9',amber,2)
 path(f'M{x-38} {y-31} Q{x} {y-69} {x+38} {y-31}',fill='none',stroke=amber,sw=3,dash='7 6')
# rail along upper deck, diagrammatic only
rect(391,586,544,13,metal,metal,1,4)
# printed removable bridge
rect(417,568,514,18,blue,teal,3,4)
for x in [431,903]:
 rect(x,586,18,10,'#C6DAE0',teal,2)
# Camera QR, antirotation saddle, body and lens
rect(465,552,155,15,palePurple,purple,2,3)
path('M468 551 L468 535 L614 535 L614 551',palePurple,purple,3)
rect(490,462,115,72,'#2F3947','#172536',2,8)
rect(493,451,36,13,'#45566A','#172536',2,3)
rect(409,476,81,51,'#44556B','#172536',2,4)
rect(393,480,18,43,'#6C7F95','#172536',2,2)
text(549,501,'SONY',17,'white','bold','middle')
# lens keepout outline
rect(365,463,126,77,'none',amber,2,8,'7 5')
# pole and braced mount
rect(848,426,67,140,blue,teal,3,5)
path('M778 565 L847 457 L847 565 Z',blue,teal,3)
rect(871,329,15,229,'#54677A',metal,2,4)
rect(875,270,7,59,'#8393A3',metal,1,2)
line(878,263,878,248,metal,5,'6 4')
# camera head with icon
rect(862,212,33,49,'#2F3947','#172536',2,8)
circle(878,225,7,'#94BBC7','#172536',1.5)
# clamps separated on one lower fixed tube
for y in [438,522]:
 rect(850,y,58,20,'#C9DAE1',teal,3,5)
 circle(901,y+10,4,metal)
# Telescoping collar
rect(866,325,25,10,'#344B60','#344B60',2,3)
# Side annotations
badge(509,367,'A',purple)
lines(539,360,['ZV-E1 + 18–50 mm lens','Exact lens envelope TBD'],23,ink,29)
path('M540 398 L540 438',stroke=purple,sw=2)
text(78,382,'Low metal quick release',23,purple,'bold')
text(78,411,'+ anti-rotation saddle',23,purple)
path('M301 407 L329 407 L432 551 L465 551',stroke=purple,sw=2)
badge(688,290,'B')
lines(718,280,['X6 / 196 g','114 cm stick','Use height TBD'],22,ink,27)
path('M820 257 L839 242 L861 239',stroke=teal,sw=2)
lines(961,375,['Two clamps,','one fixed','lower tube'],22,teal,28,'bold')
path('M951 399 L928 399 L908 448',stroke=teal,sw=2)
path('M951 432 L928 432 L908 532',stroke=teal,sw=2)
text(705,488,'Brace',22,teal,'bold')
path('M755 493 L801 523',stroke=teal,sw=2)
# deck label below schematic
lines(74,738,['Keep native','perception clear'],22,amber,27,'bold')
path('M172 717 L160 669',stroke=amber,sw=2)
text(530,770,'No downward wrap',23,teal,'bold')
text(530,800,'over either battery door',22,teal)
path('M715 744 L715 707',stroke=teal,sw=2)
text(76,853,'Pole shown shortened; placement and camera clearance are provisional.',21,muted)
# TOP VIEW CARD
rect(1156,178,600,700,'white','#DDE4EA',1.5,20)
text(1188,223,'02   TOP VIEW',27,ink,'bold')
text(1188,256,'Both batteries withdraw from the same side',22,muted)
# top body
path('M1379 309 L1515 309 L1584 385 L1602 639 L1542 727 L1363 727 L1302 639 L1321 385 Z',body,'#98A7B5',3)
# native sensor zones front rear
rect(1387,289,121,38,paleAmber,amber,2,18)
rect(1387,711,121,38,paleAmber,amber,2,18)
text(1447,315,'KEEP CLEAR',15,amber,'bold','middle')
text(1447,738,'KEEP CLEAR',15,amber,'bold','middle')
line(1640,363,1640,293,muted,3,marker='arrow');text(1698,332,'FRONT',18,muted,'bold','middle')
# battery zones and side access arrows
rect(1602,474,43,140,paleAmber,'#E4C893',1,3)
for xx in [1602]:
 for yy in range(484,605,17):line(xx+4,yy+8,xx+38,yy-8,'#E5B86D',2)
line(1616,540,1710,540,amber,3,marker='arrow')
text(1690,580,'OUT',17,amber,'bold')
# rails
for x in [1350,1540]:rect(x,357,13,320,metal,metal,1,4)
# two crossmembers connected longitudinal spine, illustrative positions
rect(1334,417,233,24,blue,teal,3,5)
rect(1334,614,233,24,blue,teal,3,5)
rect(1402,441,28,173,blue,teal,3,4)
rect(1473,441,28,173,blue,teal,3,4)
# sliding nuts metal at rail/crossmember crossings
for x in [1346,1536]:
 for y in [420,617]:
  rect(x,y,21,18,'#8AA0B0',metal,1,2);circle(x+10.5,y+9,4,'#F6F9FB',metal,1)
# Sony top, lens toward front
rect(1390,450,119,66,'#2F3947','#172536',2,8)
rect(1417,410,62,41,'#44556B','#172536',2,3)
text(1448,489,'SONY',18,'white','bold','middle')
# Pole rear of camera centerline; circle fit conceptual
circle(1448,592,29,blue,teal,3)
circle(1448,592,9,metal)
line(1448,350,1448,679,'#9CACB7',1.5,'7 6')
# dimension below body
line(1356.5,761,1356.5,788,muted,1.5)
line(1546.5,761,1546.5,788,muted,1.5)
line(1356.5,777,1546.5,777,muted,2)
arrow_head(1546.5,777,1356.5,777,muted)
arrow_head(1356.5,777,1546.5,777,muted)
text(1451.5,808,'213 mm rail spacing / OEM',21,ink,'bold','middle')
text(1188,852,'Hardware positions along rails are illustrative.',20,muted)
# LOAD PATH CARD
rect(44,902,1712,288,'white','#DDE4EA',1.5,20)
text(76,948,'03   MECHANICAL LOAD PATH',27,ink,'bold')
text(1724,948,'No final fastener length, thread engagement or strength claim',20,muted,'normal','end')
# path rows, same shared bridge
rect(78,979,330,72,palePurple,'#CFBEDF',1.5,12)
text(243,1008,'Sony + lens',24,purple,'bold','middle')
text(243,1036,'metal QR + anti-rotation saddle',19,purple,'normal','middle')
rect(78,1066,330,72,blue,'#B0D5DD',1.5,12)
text(243,1095,'X6 + telescopic pole',24,teal,'bold','middle')
text(243,1123,'two clamps + brace',20,teal,'normal','middle')
line(410,1015,458,1015,muted,2.5);line(410,1102,458,1102,muted,2.5);line(458,1015,458,1102,muted,2.5);line(458,1059,508,1059,muted,3,marker='arrow')
rect(520,1006,324,107,blue,teal,2,12)
text(682,1045,'Printed bridge /',25,teal,'bold','middle')
text(682,1076,'cross-member module(s)',24,teal,'bold','middle')
line(851,1059,899,1059,muted,3,marker='arrow')
rect(910,1006,356,107,'#E9EEF2','#BAC7D2',2,12)
text(1088,1045,'Metal M6 bolts + supplied',24,ink,'bold','middle')
text(1088,1076,'low-profile sliding nuts',24,ink,'bold','middle')
line(1273,1059,1320,1059,muted,3,marker='arrow')
rect(1332,1006,382,107,'#F1F4F6','#BAC7D2',2,12)
text(1523,1045,'Factory rails → A2 chassis',24,ink,'bold','middle')
text(1523,1076,'verified interface; fit still required',20,muted,'normal','middle')
text(520,1160,'Optional metal pole-base stud only after the stick’s base thread is verified.',22,muted)
# BOTTOM DECISIONS
rect(44,1214,1712,320,'#EAF0F3','#D6E1E7',1.5,20)
text(76,1260,'DESIGN ENVELOPE & OPEN ITEMS',27,ink,'bold')
# three columns
line(598,1290,598,1497,'#CCD8E0',2);line(1167,1290,1167,1497,'#CCD8E0',2)
text(78,1307,'PRINTABLE MODULES',21,teal,'bold')
lines(78,1348,['H2S build volume: 340 × 320 × 340 mm','Provisional module footprint: ≤280 × 280 mm','Allow room for brims and print orientation.','No final plate thickness or module size yet.'],21,ink,34)
text(626,1307,'PRESERVE ACCESS & VIEWS',21,teal,'bold')
lines(626,1348,['Preserve both batteries’ side extraction.','Keep legs, sensors and ventilation clear.','Use real metal capture hardware;','M6×14 is not assumed to fit this stack.'],21,ink,34)
text(1195,1307,'MEASURE BEFORE CAD',21,teal,'bold')
lines(1195,1348,['Exact 18–50 mm lens model and mass','Pole tube diameter, fixed-tube length,','thread, working height and clamp spacing','Validate vibration, leverage and retention.'],21,ink,34)
text(76,1510,'A design discussion sheet. Final geometry, materials, fasteners, fit and load capacity remain to be engineered.',21,muted)
text(44,1564,'A2 CAMERA RIG / ASSET & CONCEPT PHASE',19,muted,'bold')
text(1756,1564,'Sources and verification notes accompany this sheet.',19,muted,'normal','end')
add('</svg>')
(P/'a2-camera-rig-concept.svg').write_text('\n'.join(s))
print(P/'a2-camera-rig-concept.svg')
