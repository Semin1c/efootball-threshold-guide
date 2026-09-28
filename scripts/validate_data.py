#!/usr/bin/env python3
"""Validate relational integrity and recommended target bounds before publishing."""
import datetime, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'site/thresholds.json').read_text())
assert d['schemaVersion']==1
for key in ('lastUpdated','lastSourceReview'): datetime.date.fromisoformat(d[key])
def ids(key):
    values=[x['id'] for x in d[key]]
    assert len(values)==len(set(values)),f'Duplicate IDs in {key}'
    return set(values)
p,a,s,c=(ids(k) for k in ('positions','attributes','sources','confidenceLevels'))
assert p=={'CF','SS','LWF','RWF','AMF','CMF','DMF','LB','RB','CB','GK'}
assert len(a)==26
for pos in d['positions']:
    assert set(pos.get('priorityAttributes',[])) <= a
seen=set()
for attr in d['attributes']:
    assert attr['confidence'] in c
    assert set(attr['sourceIds'])<=s
    assert attr['threshold']['label'] and attr['threshold']['scope'] and attr['practical']
    datetime.date.fromisoformat(attr['lastReviewed'])
for record in d['records']:
    key=(record['position'],record['attribute'])
    assert key not in seen and key[0] in p and key[1] in a
    seen.add(key)
    assert record['targetConfidence']=='heuristic'
    assert set(record['sourceIds'])<=s
    target=record['target']
    if target is not None:
        assert len(target)==2 and all(isinstance(v,int) for v in target)
        assert 40<=target[0]<=target[1]<=110
        assert record['targetStatus']=='recommended'
    else: assert record['targetStatus'] in ('retain-base','not-applicable')
assert seen=={(pos,attr) for pos in p for attr in a},'Missing position/attribute combinations'
for source in d['sources']:
    assert source['url'] is None or source['url'].startswith('https://')
for memo in d['memorize']: assert set(memo['sourceIds'])<=s
print(f'Valid: {len(p)} positions × {len(a)} attributes = {len(seen)} records.')
