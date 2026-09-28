#!/usr/bin/env python3
"""Read-only evidence monitor. Writes reports/candidate snapshots, never the chart."""
import argparse, datetime, difflib, hashlib, html, json, re, sys
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 3_000_000
KEYWORDS = re.compile(r'awareness|speed|acceleration|threshold|dribbl|possession|heading|keeper|stamina|passing|balance|v[0-9]+\.', re.I)
class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript'): self.skip += 1
        if tag in ('p','li','h1','h2','h3','h4','br','article'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript') and self.skip: self.skip -= 1
    def handle_data(self, text):
        if not self.skip: self.parts.append(text)

def normalize(raw):
    parser=TextParser(); parser.feed(raw)
    lines=[re.sub(r'\s+',' ',html.unescape(x)).strip() for x in ''.join(parser.parts).splitlines()]
    return '\n'.join(x for x in lines if x)

def retrieve(source):
    # Only URLs in the local, human-vetted config are requested. No page-supplied URLs are followed.
    try:
        req=Request(source['url'],headers={'User-Agent':'ThresholdFieldGuide/1.0 (public evidence review; weekly check)'})
        with urlopen(req,timeout=20) as response:
            content=response.read(MAX_BYTES+1)
            if len(content)>MAX_BYTES: raise ValueError('Page exceeds size limit')
            raw=content.decode(response.headers.get_content_charset() or 'utf-8',errors='replace')
        text=normalize(raw)
        if len(text)<100 or re.search(r'just a moment|verify you are human|blocked by network security',text[:1200],re.I):
            raise ValueError('Blocked, challenge page, or unexpectedly empty response')
        # Keep bounded excerpts for local review; complete original remains at the source URL.
        relevant='\n'.join(line[:1200] for line in text.splitlines() if KEYWORDS.search(line))[:24000]
        if not relevant: raise ValueError('No relevant text extracted; inspect page/parser manually')
        return source['id'],dict(url=source['url'],sha256=hashlib.sha256(relevant.encode()).hexdigest(),text=relevant)
    except Exception as exc:
        return source['id'],dict(error=str(exc),url=source['url'])

def compare(old, current):
    if 'error' in current: return 'FETCH_ERROR'
    if old is None: return 'BASELINE_NEEDED'
    return 'UNCHANGED' if old.get('sha256') == current['sha256'] and old.get('url') == current['url'] else 'REVIEW_CHANGE'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,default=ROOT/'sources-watch.json')
    ap.add_argument('--baseline',type=Path,default=ROOT/'review/baseline.json')
    ap.add_argument('--output',type=Path,default=ROOT/'review/latest')
    ap.add_argument('--fixtures',type=Path,help='Offline test JSON mapping IDs to {text: ...} or {error: ...}')
    ap.add_argument('--accept-candidate',type=Path,help='Explicit reviewer action: accept this candidate snapshot as the next baseline; does NOT update chart data')
    args=ap.parse_args()
    if args.accept_candidate:
        candidate=json.loads(args.accept_candidate.read_text())
        if candidate.get('schemaVersion') != 1 or not isinstance(candidate.get('sources'),dict): raise ValueError('Invalid candidate')
        args.baseline.parent.mkdir(parents=True,exist_ok=True)
        args.baseline.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
        print('Baseline accepted explicitly. Chart untouched.');return 0
    config=json.loads(args.config.read_text())
    watched=config['sources']
    for s in watched:
        if not s['url'].startswith('https://') or not re.fullmatch(r'[a-z0-9-]+',s['id']): raise ValueError('Invalid vetted source')
    baseline=json.loads(args.baseline.read_text()) if args.baseline.exists() else {'schemaVersion':1,'sources':{}}
    if args.fixtures:
        fixtures=json.loads(args.fixtures.read_text()); fetched={}
        for s in watched:
            value=fixtures.get(s['id'],{'error':'Missing fixture'})
            fetched[s['id']]=dict(value,url=s['url'])
            if 'error' not in value: fetched[s['id']]['sha256']=hashlib.sha256(value['text'].encode()).hexdigest()
    else:
        with ThreadPoolExecutor(max_workers=3) as pool: fetched=dict(pool.map(retrieve,watched))
    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    candidate={'schemaVersion':1,'checkedAt':timestamp,'sources':dict(baseline['sources'])}
    report={'checkedAt':timestamp,'reviewRequired':False,'results':[]}
    out=['# Source review report',f'Checked: {timestamp}','', 'Source differences are untrusted review signals, not threshold updates. The published JSON was not changed.','']
    args.output.mkdir(parents=True,exist_ok=True)
    for s in watched:
        current=fetched[s['id']]; previous=baseline['sources'].get(s['id']); status=compare(previous,current)
        report['results'].append({'id':s['id'],'url':s['url'],'status':status,'error':current.get('error')})
        report['reviewRequired'] |= status != 'UNCHANGED'
        out += [f"## {s['id']} — {status}",f"Source: {s['url']}",'']
        if status=='FETCH_ERROR': out += [f"Fetch failed: {current['error']}",'Last successful baseline retained. Open the source manually; do not infer no change.','']
        else:
            candidate['sources'][s['id']]=current
            if status in ('REVIEW_CHANGE','BASELINE_NEEDED'):
                # Plain-text files, not rendered source HTML, reduce injection risk during review.
                diff='\n'.join(difflib.unified_diff((previous or {}).get('text','').splitlines(),current['text'].splitlines(),fromfile='baseline',tofile='candidate',lineterm=''))
                (args.output/(s['id']+'.diff.txt')).write_text(diff+'\n')
                out += ['Inspect the attached plain-text diff and original source. Confirm version, platform and method.','']
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (args.output/'report.md').write_text('\n'.join(out))
    (args.output/'candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
    print('\n'.join(f"{r['id']}: {r['status']}" for r in report['results']))
    # Nonzero signals pending review in Actions; report upload runs with always().
    return 2 if report['reviewRequired'] else 0
if __name__=='__main__': sys.exit(main())
