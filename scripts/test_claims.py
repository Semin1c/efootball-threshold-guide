#!/usr/bin/env python3
import json, tempfile, subprocess, sys
from pathlib import Path
from update_claims import merge, extract, safe_url, ROOT
now='2026-09-28T12:00:00+00:00'
doc=dict(url='https://www.reddit.com/r/Amadeusz/comments/example/test/',text='Speed threshold is 96 in v6.0.0.\nA controlled test would be needed.',type='community-test',publishedAt='2026-09-28')
checks=[dict(source='fixture',url=doc['url'],ok=True)]
r,n=merge({},[doc],checks,now);assert n==1 and r['claims'][0]['confidence']=='provisional'
r2,n=merge(r,[doc],checks,now);assert n==0 and len(r2['claims'])==1
changed=dict(doc,text='Speed threshold is 95 in v6.0.1.')
r3,n=merge(r2,[changed],checks,now);assert n==1 and r3['claims'][0]['supersedes']==r['claims'][0]['id']
assert len(r3['claims'])==2
r4,n=merge(r3,[],[dict(ok=False)],now);assert r4['health']=='unavailable' and r4['claims']==r3['claims']
assert extract(dict(text='I like this player and his speed.')) is None
assert not safe_url('javascript:alert(1)') and not safe_url('https://www.reddit.com.evil.test/')
assert len(r['claims'][0]['excerpt'].split())<=20
original=(ROOT/'site/thresholds.json').read_bytes()
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'fixtures.json').write_text(json.dumps(dict(docs=[doc],checks=checks)))
 subprocess.run([sys.executable,str(ROOT/'scripts/update_claims.py'),'--fixtures',str(p/'fixtures.json'),'--output',str(p/'out.json')],check=True)
assert (ROOT/'site/thresholds.json').read_bytes()==original
print('Claim tests passed: extraction, deduplication, revision history, failed-source retention, safe URLs, chart preservation.')
