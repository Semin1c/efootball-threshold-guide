'use strict';
(() => {
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date = s => new Date(s + 'T12:00:00Z').toLocaleDateString('en-GB', {day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
let feed = null, showAllClaims = false;
let data, state = {position:'CF',attribute:'all',confidence:'all',q:''};
function ref(id) { const s = data.sources.find(s => s.id === id); return s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a>` : `<span>${esc(s.title)}</span>`; }
function badge(a) {return `<span class="badge ${esc(a.confidence)}">${esc(data.confidenceLevels.find(c => c.id === a.confidence).label)}</span>`;}
function syncUrl() {const p = new URLSearchParams();Object.entries(state).forEach(([k,v]) => {if(v && v !== 'all') p.set(k,v);});history.replaceState(null,'',`${location.pathname}?${p}${location.hash}`);}
function render() {
 const position = data.positions.find(p => p.id === state.position);
 $('mobile-position').value = state.position;
 $('role-kicker').textContent = 'POSITION GUIDE / ' + position.id;
 $('role-title').textContent = position.name; $('role-summary').textContent = position.summary;
 $('role-note').textContent = position.note; $('role-badge').textContent = position.id;
 document.querySelectorAll('.position-button').forEach(b => b.setAttribute('aria-pressed',String(b.dataset.position === state.position)));
 const tokens = state.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
 const rows = data.records.filter(r => {
  if (r.position !== state.position || (state.attribute !== 'all' && state.attribute !== r.attribute)) return false;
  const a = data.attributes.find(a => a.id === r.attribute);
  if (state.confidence !== 'all' && a.confidence !== state.confidence) return false;
  const hay = [position.id,position.name,a.name,a.group,a.threshold.label,a.threshold.note,a.threshold.scope,a.practical,r.targetNote,...a.sourceIds.map(id => data.sources.find(s => s.id===id).title)].join(' ').toLowerCase();
  return tokens.every(t => hay.includes(t));
 }).sort((a,b)=>{const order=position.priorityAttributes||[];const rank=id=>order.includes(id)?order.indexOf(id):order.length;return rank(a.attribute)-rank(b.attribute);});
 $('result-count').textContent = `${rows.length} of ${data.attributes.length} attributes`;
 $('empty').hidden = rows.length > 0;
 $('results').innerHTML = rows.map(r => {
  const a = data.attributes.find(a=>a.id===r.attribute);
  const target = r.target ? `<span class="target-value">${r.target[0]}–${r.target[1]}</span><span class="range-track" aria-hidden="true"><i style="left:${r.target[0]-40}%;width:${r.target[1]-r.target[0]}%"></i></span>` : `<span class="target-value text-target">${r.targetStatus==='not-applicable'?'Not applicable':'Retain base'}</span>`;
  const refs = [...new Set([...a.sourceIds,...r.sourceIds])];
  return `<details class="stat-row"><summary class="row-summary"><span><span class="attr-name">${esc(a.name)}</span><span class="attr-group">${esc(a.group)}</span></span><span>${target}<span class="target-caption">${r.target?'recommended target':'no spending target'}</span></span><span class="evidence-cell"><span class="threshold-label">${esc(a.threshold.label)}</span>${badge(a)}</span><span class="expand" aria-hidden="true">+</span></summary><div class="row-detail"><div><h4>Practical build advice</h4><p>${esc(r.practical || a.practical)}</p><p>${esc(r.targetNote)}</p></div><div><h4>What the evidence says</h4><p class="scope">${esc(a.threshold.scope)}</p><p>${esc(a.threshold.note)}</p></div><div class="evidence-detail"><h4>Sources & review notes</h4><ul>${refs.map(id => {const s=data.sources.find(s=>s.id===id);return `<li class="source-ref">${ref(id)}<p>${esc(s.note)}</p></li>`;}).join('')}</ul><p class="scope">Reviewed ${date(a.lastReviewed)} · Target confidence: heuristic · ${esc(data.reviewScope)}</p></div></div></details>`;
 }).join('');
 renderClaims();
 syncUrl();
}
function renderClaims() {
 if(!feed) return;
 const q=state.q.toLowerCase().trim();
 const claims=feed.claims.filter(c=>(state.attribute==='all'||c.attributeIds.includes(state.attribute)) && (state.confidence==='all'||state.confidence==='provisional') && (!q||q.split(/\s+/).every(t=>[c.title,c.excerpt,c.engineMention,...c.attributeIds].join(' ').toLowerCase().includes(t))));
 const visible=showAllClaims?claims:claims.slice(0,6);
 const safeLink=url=>{try{const u=new URL(url);return u.protocol==='https:'&&['www.konami.com','www.reddit.com','reddit.com'].includes(u.hostname)?u.href:null;}catch{return null;}};
 $('claim-list').innerHTML=visible.length?visible.map(c=>{
  const url=safeLink(c.sourceUrl);const newer=feed.claims.some(n=>n.supersedes===c.id);
  return `<article class="claim-card"><div><span class="badge provisional">Provisional · auto-added</span>${newer?'<span class="revision-label">Earlier source revision</span>':''}</div><h3>${esc(c.title)}</h3><blockquote>${esc(c.excerpt)}…</blockquote><p class="claim-meta">${esc(c.sourceType)} · Discovered ${date(c.discoveredAt.slice(0,10))}${c.sourcePublishedAt?' · Source dated '+esc(c.sourcePublishedAt.slice(0,10)):''}</p><p class="claim-meta">Engine mentioned: ${esc(c.engineMention||'not specified')} · Platform unverified</p>${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Read original source ↗</a>`:''}${c.supersedes?'<p class="claim-meta">New source revision; previous finding retained in this feed.</p>':''}</article>`;
 }).join(''):'<p class="empty-claims">No provisional findings match these filters. Existing recommendations remain available above.</p>';
 $('more-claims').hidden=claims.length<=6;
 $('more-claims').textContent=showAllClaims?'Show latest six':`Show all ${claims.length} findings`;
}
async function loadClaims() {
 try {
  const r=await fetch('provisional.json',{cache:'no-cache'});if(!r.ok)throw new Error('Unavailable');
  feed=await r.json();if(feed.schemaVersion!==1||!Array.isArray(feed.claims)||!Array.isArray(feed.checks))throw new Error('Invalid feed');
  const ok=feed.checks.filter(c=>c.ok).length;
  const when=feed.lastCheck?new Date(feed.lastCheck).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}):'not yet run';
  $('watch-status').textContent=`Last automatic check: ${when}. ${ok} of ${feed.checks.length} sources reached. ${feed.claims.length} findings retained.${feed.health==='partial'?' Some sources unavailable.':feed.health==='unavailable'?' Sources unavailable; previous findings preserved.':''}`;
  $('watch-details').innerHTML='<p>Checks are source retrieval attempts, not gameplay verification. Old findings remain visible when a source is unavailable.</p>'+feed.checks.map(c=>`<p><strong>${c.ok?'Reached':'Unavailable'}</strong> · ${esc(c.source)}${c.ok?'':' — '+esc(c.error||'Fetch failed')}</p>`).join('');
  renderClaims();
 } catch { $('watch-status').textContent='The provisional feed could not load. Reviewed recommendations above are still available.'; }
}
function reset(){state.attribute='all';state.confidence='all';state.q='';$('search').value='';$('attribute').value='all';$('confidence').value='all';render();}
async function init() {
 try {
  const response = await fetch('thresholds.json', {cache:'no-cache'});
  if (!response.ok) throw new Error(`Data request failed (${response.status})`);
  data = await response.json();
  if(data.schemaVersion!==1 || !Array.isArray(data.records)) throw new Error('Unsupported data format');
  const params = new URLSearchParams(location.search);
  if (data.positions.some(p=>p.id===params.get('position'))) state.position=params.get('position');
  if (data.attributes.some(a=>a.id===params.get('attribute'))) state.attribute=params.get('attribute');
  if (data.confidenceLevels.some(c=>c.id===params.get('confidence'))) state.confidence=params.get('confidence');
  state.q=(params.get('q')||'').slice(0,300);
  $('updated').textContent=date(data.lastUpdated);$('review-date').textContent=date(data.lastSourceReview);$('engine').textContent=data.engineBaseline+' BASELINE';
  $('position-buttons').innerHTML=data.positions.map(p=>`<button type="button" class="position-button" data-position="${esc(p.id)}" aria-pressed="false" aria-label="${esc(p.id+' · '+p.name)}"><strong>${esc(p.id)}</strong><span>${esc(p.name)}</span></button>`).join('');
  $('mobile-position').innerHTML=data.positions.map(p=>`<option value="${esc(p.id)}">${esc(p.id+' · '+p.name)}</option>`).join('');
  $('mobile-position').addEventListener('change',e=>{state.position=e.target.value;render();});
  $('position-buttons').addEventListener('click',e=>{const b=e.target.closest('button');if(b){state.position=b.dataset.position;render();}});
  $('attribute').innerHTML+=[...data.attributes].sort((a,b)=>a.name.localeCompare(b.name)).map(a=>`<option value="${esc(a.id)}">${esc(a.name)}</option>`).join('');
  $('confidence').innerHTML+=data.confidenceLevels.map(c=>`<option value="${esc(c.id)}">${esc(c.label)}</option>`).join('');
  $('attribute').value=state.attribute;$('confidence').value=state.confidence;$('search').value=state.q;
  ['attribute','confidence'].forEach(id=>$(id).addEventListener('change',e=>{state[id]=e.target.value;render();}));
  $('search').addEventListener('input',e=>{state.q=e.target.value.slice(0,300);render();});
  $('filters').addEventListener('submit',e=>e.preventDefault());$('reset').addEventListener('click',reset);$('empty-reset').addEventListener('click',reset);
  $('memo-cards').innerHTML=data.memorize.map(m=>`<article class="memo-card"><strong>${esc(m.number)}</strong><h4>${esc(m.title)}</h4><p>${esc(m.text)}</p></article>`).join('');
  $('confidence-key').innerHTML=data.confidenceLevels.map(c=>`<div><span class="badge ${esc(c.id)}">${esc(c.label)}</span><p>${esc(c.description)}</p></div>`).join('');
  $('traits').innerHTML=data.fixedTraits.map(t=>`<p><strong>${esc(t.name)}.</strong> ${esc(t.note)}</p>`).join('');
  $('source-list').innerHTML=data.sources.map((s,i)=>`<article class="source-entry" id="source-${esc(s.id)}"><span class="source-index">${String(i+1).padStart(2,'0')}</span><div>${ref(s.id)}<p>${esc(s.note)}</p><div class="source-meta">${esc(s.type)} · ${esc(s.scope)}<br>${s.publishedAt?'Published '+date(s.publishedAt)+' · ':''}Checked ${date(s.lastChecked)}</div></div></article>`).join('');
  render();$('status').hidden=true;$('app').hidden=false;
  $('more-claims').addEventListener('click',()=>{showAllClaims=!showAllClaims;renderClaims();});
  loadClaims();
 } catch (error) {
  $('status').setAttribute('role','alert');
  $('status').innerHTML='<h1>The guide could not load</h1><p>Serve the site through a local web server or upload the site folder to your host. Keep thresholds.json beside index.html.</p><button type="button" id="retry">Try again</button> <a href="thresholds.json">Open data</a>';
  $('retry').addEventListener('click',()=>location.reload());
 }
}
init();
})();
