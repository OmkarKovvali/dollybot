import base64, hashlib, json, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TREE=json.loads((ROOT/'github-repository-tree.json').read_text())
REV=json.loads((ROOT/'github-a2-commits.json').read_text())[0]['sha']
items=[x for x in TREE['tree'] if x['type']=='blob' and x['path'].startswith('robots/a2_description/')]
items += [x for x in TREE['tree'] if x['path']=='LICENSE']
def fetch(x):
    rel=x['path'].removeprefix('robots/a2_description/')
    url=f'https://raw.githubusercontent.com/unitreerobotics/unitree_ros/{REV}/{x["path"]}'
    p=ROOT/'official-a2'/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    b=urllib.request.urlopen(url).read()
    p.write_bytes(b)
    return {'path':str(p.relative_to(ROOT)),'source_url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'upstream_blob_sha':x['sha']}
with ThreadPoolExecutor(max_workers=6) as pool: result=list(pool.map(fetch,items))
(ROOT/'download-manifest.json').write_text(json.dumps({'retrieved_date':'2026-11-23','repository':'https://github.com/unitreerobotics/unitree_ros','repository_head':TREE['sha'],'a2_latest_commit':REV,'a2_latest_commit_date':'2026-06-09T09:16:08Z','assets':result},indent=2)+'\n')
print(f'Downloaded {len(result)} files, {sum(x["bytes"] for x in result):,} bytes')
