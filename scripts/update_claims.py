#!/usr/bin/env python3
"""Publish source candidates as provisional; never modify reviewed thresholds."""
import argparse, datetime, hashlib, json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from html.parser import HTMLParser
from check_sources import normalize
ROOT=Path(__file__).resolve().parents[1]
FEED='https://www.reddit.com/r/Amadeusz/new/.rss'
HOME='https://www.konami.com/efootball/en/'
ALLOWED={'www.konami.com','www.reddit.com','reddit.com'}
SIGNAL=re.compile(r'threshold|breakpoint|diminish|benefit curve|rate of return|no difference|animation|made changes|adjusted|revised',re.I)
ATTRS={
 'offensive-awareness':r'offensive awareness', 'defensive-awareness':r'defensive awareness',
 'ball-control':r'ball control','tight-possession':r'tight possession','dribbling':r'dribbl\w*',
 'low-pass':r'low pass|through pass\w*','lofted-pass':r'lofted pass|crossing',
 'finishing':r'finishing','heading':r'heading|header','set-piece-taking':r'set piece',
 'curl':r'curl','speed':r'\bspeed\b','acceleration':r'acceleration',
 'kicking-power':r'kicking power|shot power','jumping':r'jump\w*',
 'physical-contact':r'physical contact|shielding','balance':r'\bbalance\b','stamina':r'stamina',
 'tackling':r'tackl\w*','aggression':r'aggression','defensive-engagement':r'defensive engagement',
 'gk-awareness':r'gk awareness','gk-catching':r'gk catching|goalkeeper|keeper|catching',
 'gk-parrying':r'gk parrying|parrying','gk-reflexes':r'gk reflexes','gk-reach':r'gk reach'}

def safe_url(url):
    p=urlparse(url)
    return p.scheme=='https' and p.hostname in ALLOWED and not p.username and not p.password

def fetch(url):
    if not safe_url(url): raise ValueError('URL outside vetted sources')
    req=Request(url,headers={'User-Agent':'ThresholdFieldGuide/1.1 (personal public-source reference)'})
    with urlopen(req,timeout=18) as r:
        if not safe_url(r.url): raise ValueError('Redirect outside vetted sources')
        raw=r.read(3_000_001)
        if len(raw)>3_000_000: raise ValueError('Response too large')
        return raw.decode(r.headers.get_content_charset() or 'utf-8',errors='replace')

def article_text(raw,url):
    # Reddit's main post only: never turn comments/sidebar suggestions into a claim.
    if 'reddit.com' in url:
        match=re.search(r'<shreddit-post\b.*?</shreddit-post>',raw,re.S|re.I)
        if not match: raise ValueError('Cannot isolate original Reddit post; manual source review needed')
        raw=match.group(0)
    text=normalize(raw)
    if 'konami.com' in url and 'INFO DETAIL' in text:
        text=text.split('INFO DETAIL',1)[1]
        text=re.split(r'\n(?:Back|HOME|Privacy Policy)\b',text,1)[0]
    if len(text)<100 or re.search(r'blocked by network security|verify you are human|just a moment',text[:1000],re.I):
        raise ValueError('Source blocked or extraction incomplete')
    return text[:100000]

def source_date(text):
    m=re.search(r'\b(\d{2})/(\d{2})/(20\d{2})\s+Update',text)
    if not m:return None
    day,month,year=m.groups()
    try:return datetime.date(int(year),int(month),int(day)).isoformat()
    except ValueError:return None

def extract(doc):
    text=doc['text']; lines=re.split(r'(?<=[.!?])\s+|\n',text)
    candidates=[]
    for line in lines:
        if not SIGNAL.search(line):continue
        attrs=[key for key,pattern in ATTRS.items() if re.search(pattern,line,re.I)]
        if attrs:candidates.append((line,attrs))
    if not candidates:return None
    # One candidate per source revision; short quotation, no invented numeric rule.
    line,attrs=next(((line,attrs) for line,attrs in candidates if re.search(r'threshold|breakpoint|diminish|rate of return',line,re.I)),candidates[0])
    words=line.split(); signal=SIGNAL.search(line)
    start=max(0,len(line[:signal.start()].split())-7) if len(words)>20 else 0
    excerpt=('… ' if start else '')+' '.join(words[start:start+19])
    version=re.search(r'\bv[456]\.[0-9]+(?:\.[0-9]+)?\b',text,re.I)
    return dict(attributeIds=attrs,excerpt=excerpt,engineMention=version.group(0) if version else None)

def merge(old,docs,checks,now):
    claims=list(old.get('claims',[])); seen={c['id'] for c in claims}; new=0
    latest={c['sourceUrl']:c for c in reversed(claims)}
    for doc in docs:
        if not safe_url(doc['url']):continue
        item=extract(doc)
        if not item:continue
        signature=hashlib.sha256((doc['url']+'\n'+json.dumps(item,sort_keys=True)).encode()).hexdigest()[:24]
        if signature in seen:continue
        previous=latest.get(doc['url'])
        claim=dict(id=signature,confidence='provisional',discoveredAt=now,sourcePublishedAt=doc.get('publishedAt'),sourceUrl=doc['url'],sourceType=doc['type'],title='Potential '+', '.join(x.replace('-',' ') for x in item['attributeIds'][:3])+' finding',**item,
                   platform='Not independently verified',method='Automatic text matching; not independent gameplay testing',supersedes=previous['id'] if previous else None)
        claims.insert(0,claim);seen.add(signature);latest[doc['url']]=claim;new+=1
    return dict(schemaVersion=1,lastCheck=now,lastAddition=now if new else old.get('lastAddition'),health='ok' if checks and all(x['ok'] for x in checks) else 'partial' if any(x['ok'] for x in checks) else 'unavailable',checks=checks,claims=claims),new

class NewsLinks(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href','');url=urljoin(HOME,href)
            if re.fullmatch(r'https://www\.konami\.com/efootball/en/topic/news/\d+/?',url) and url not in self.links:self.links.append(url)

def collect(watched):
    docs=[];checks=[]
    try:
        xml=ET.fromstring(fetch(FEED));ns={'a':'http://www.w3.org/2005/Atom'}
        if xml.tag!='{http://www.w3.org/2005/Atom}feed':raise ValueError('Unexpected feed format')
        for entry in xml.findall('a:entry',ns)[:50]:
            link=entry.find('a:link',ns);url=link.get('href','') if link is not None else ''
            text=normalize((entry.findtext('a:title','',ns))+'\n'+entry.findtext('a:content','',ns))
            if safe_url(url):docs.append(dict(url=url,text=text,type='community-feed',publishedAt=entry.findtext('a:published',None,ns)))
        checks.append(dict(source='Amadeusz discovery feed',url=FEED,ok=True))
    except Exception as e:checks.append(dict(source='Amadeusz discovery feed',url=FEED,ok=False,error=str(e)))
    urls={s['url'] for s in watched if s['id'] not in ('konami-news','amadeusz-new')}
    try:
        parser=NewsLinks();parser.feed(fetch(HOME))
        if not parser.links:raise ValueError('No news links found; manual review needed')
        urls.update(parser.links[:8]);checks.append(dict(source='KONAMI news discovery',url=HOME,ok=True))
    except Exception as e:checks.append(dict(source='KONAMI news discovery',url=HOME,ok=False,error=str(e)))
    def read(url):
        try:
            text=article_text(fetch(url),url)
            return dict(url=url,text=text,type='official' if 'konami.com' in url else 'community-test',publishedAt=source_date(text)),dict(source=url,url=url,ok=True)
        except Exception as e:return None,dict(source=url,url=url,ok=False,error=str(e))
    with ThreadPoolExecutor(max_workers=4) as pool:
        for doc,check in pool.map(read,sorted(urls)):
            if doc:docs.append(doc)
            checks.append(check)
    return docs,checks

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--fixtures',type=Path);ap.add_argument('--output',type=Path,default=ROOT/'site/provisional.json');args=ap.parse_args()
    if args.fixtures:
        fixture=json.loads(args.fixtures.read_text());docs,checks=fixture['docs'],fixture['checks']
    else:docs,checks=collect(json.loads((ROOT/'sources-watch.json').read_text())['sources'])
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    old=json.loads(args.output.read_text()) if args.output.exists() else {}
    result,added=merge(old,docs,checks,now)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'{added} provisional candidates added; {len(result["claims"])} retained. Source health: {result["health"]}. Reviewed chart untouched.')
    # Partial access is published visibly, not swallowed or treated as an empty successful scan.
    return 0
if __name__=='__main__':sys.exit(main())
