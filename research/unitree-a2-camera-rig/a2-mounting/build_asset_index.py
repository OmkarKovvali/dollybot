import pathlib, json, hashlib, shutil, html, re
p = pathlib.Path(__file__).parent
names = {
'a4ee719756e29727':'guide-rail-drawing',
'71eacf92bd051fa2':'dock-v1-dimensions',
'0fa0e7b7d5e02292':'dock-v2-dimensions',
'2a178bce74f3b92c':'dock-v2-rear-dimensions',
'ff41b795794fb6d5':'internal-hardware-block-diagram',
'0a638eeaae34e31b':'a2-component-overview',
'c8c3dc49c8ea575d':'a2-sensors-and-side-batteries',
'd8320acc2974df6c':'body-left-electrical-ports',
'67066e47eb771078':'body-right-electrical-ports',
'6c2172a77a66b679':'connector-2plus2-pin-numbering',
'153ea65282080dcf':'connector-8plus2-pin-numbering',
'c4098f82da675e92':'emergency-stop-pin-numbering',
'b0958e7a7338df63':'dock-v1-render',
'db5714c5ec5d0503':'dock-v2-render',
'e20cc13f70dfc98f':'a2-with-dock-v1',
'7f134156b8047a3b':'a2-with-dock-v2',
'd4c37d894e95eb54':'dock-right-electrical-ports',
'3836e6daad7cae86':'dock-left-electrical-ports',
'3830c38e893388c3':'dock-install-m6-nut-rail-interface'
}
rows=[]
for folder in ['about-a2-assets','dock-installation-assets']:
 data=json.loads((p/folder/'manifest.json').read_text())
 for a in data['assets']:
  old=p/folder/(a['id']+pathlib.Path(a['path']).suffix)
  if a['id'] in names:
   target=p/(names[a['id']]+old.suffix); shutil.copy2(old,target)
  else: target=old
  a['path']=str(old.resolve())
  rows.append({'file':str(target.relative_to(p)),'source_url':a['url'],'original_asset_name':a['name'],'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'origin_page':'https://support.unitree.com/home/en/A2_SDK_Development_Guide/'+('about_a2' if folder.startswith('about') else 'docking_installation')})
 (p/folder/'manifest.json').write_text(json.dumps(data,indent=2))
for name,url in [('about-a2-source.txt','https://doc-cdn.unitree.com/26/1071/en/26_1071_en'),('dock-installation-source.txt','https://doc-cdn.unitree.com/26/1424/en/26_1424_en'),('a2-manual.html','https://marketing.unitree.com/article/en/A2/User_Manual.html'),('a2-product.html','https://www.unitree.com/A2/')]:
 f=p/name
 rows.append({'file':name,'source_url':url,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(p/'assets-manifest.json').write_text(json.dumps({'retrieved_date':'2026-11-23','about_a2_page_last_updated':'2026-11-05 11:57:14 (as displayed, timezone unspecified)','manual_version':'V1.7','assets':rows},indent=2))
manual=(p/'a2-manual.html').read_text()
for i,url in enumerate(json.loads((p/'manual-page-urls.json').read_text())): manual=manual.replace(url,f'manual-pages/page-{i+1:02d}.png')
(p/'a2-manual-offline.html').write_text(manual)
# A self-contained local reference gallery; downloaded figures themselves are unchanged.
parts=['<!doctype html><html><meta charset="utf-8"><title>A2 official engineering references</title><style>body{font:17px system-ui;max-width:1250px;margin:40px auto;padding:0 24px;background:#eee;color:#111}section{background:white;padding:24px;margin:24px 0}img{display:block;max-width:100%;background:white}a{color:#135d91}p{line-height:1.5}</style><h1>Unitree A2 official engineering references</h1><p>Downloaded 23 November 2026. Source drawings are unmodified. See README.txt for interpretation and unverified details. These are interface drawings and a hardware block diagram, not a full manufacturing CAD release or circuit schematic.</p><p><a href="a2-manual-offline.html">User Manual V1.7 — all 28 official pages</a> · <a href="about-a2-source.txt">About A2 document source</a> · <a href="dock-installation-source.txt">Dock installation source</a> · <a href="README.txt">Research notes</a></p>']
for key in names:
 a=next(r for r in rows if pathlib.Path(r['file']).stem==names[key])
 title=names[key].replace('-',' ').title()
 parts += [f'<section><h2>{html.escape(title)}</h2><p><a href="{html.escape(a["source_url"])}">Original OEM image</a> · <a href="{html.escape(a["origin_page"])}">Official document page</a></p><img src="{html.escape(a["file"])}" alt="{html.escape(title)}"></section>']
parts += ['</html>']; (p/'official-references.html').write_text(''.join(parts))
print('Indexed',len(rows),'technical assets plus 28 manual pages')
