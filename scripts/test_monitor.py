#!/usr/bin/env python3
"""Offline regression checks: signal changes/errors without mutating accepted values."""
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('monitor',root/'scripts/check_sources.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.normalize('<p>Speed 90</p><script>secret()</script><p>96 &amp; 99</p>')=='Speed 90\n96 & 99'
assert m.compare(None,{'error':'403'})=='FETCH_ERROR'
assert m.compare(None,{'sha256':'x','url':'u'})=='BASELINE_NEEDED'
assert m.compare({'sha256':'x','url':'u'},{'sha256':'x','url':'u'})=='UNCHANGED'
assert m.compare({'sha256':'x','url':'u'},{'sha256':'y','url':'u'})=='REVIEW_CHANGE'
original=(root/'site/thresholds.json').read_bytes()
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp); config=p/'config.json';fixtures=p/'fixtures.json';baseline=p/'baseline.json';out=p/'out'
    config.write_text(json.dumps({'sources':[{'id':'test','url':'https://example.com/test'}]}))
    fixtures.write_text(json.dumps({'test':{'text':'Speed 90'}}))
    cmd=[sys.executable,str(root/'scripts/check_sources.py'),'--config',str(config),'--fixtures',str(fixtures),'--baseline',str(baseline),'--output',str(out)]
    assert subprocess.run(cmd,capture_output=True).returncode==2
    assert not baseline.exists()
    baseline.write_bytes((out/'candidate.json').read_bytes())
    saved=baseline.read_bytes()
    assert subprocess.run(cmd,capture_output=True).returncode==0
    fixtures.write_text(json.dumps({'test':{'text':'Speed 96'}}))
    assert subprocess.run(cmd,capture_output=True).returncode==2
    assert baseline.read_bytes()==saved
    fixtures.write_text(json.dumps({'test':{'error':'HTTP 403'}}))
    assert subprocess.run(cmd,capture_output=True).returncode==2
    assert json.loads((out/'candidate.json').read_text())['sources']==json.loads(saved)['sources']
assert (root/'site/thresholds.json').read_bytes()==original
print('Monitor checks passed: new / unchanged / changed / fetch-error; chart and baseline preserved.')
