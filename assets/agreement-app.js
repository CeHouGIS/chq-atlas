(() => {
 'use strict';
 const el=id=>document.getElementById(id),data=CHQ_AGREEMENT,models=data.models;
 const label=id=>models.find(m=>m.id===id).label,short=id=>models.find(m=>m.id===id).short;
 const count=n=>n.toLocaleString('en-GB'),pct=n=>(100*n).toFixed(1)+'%',coefficient=n=>Number.isFinite(n)?n.toFixed(3):'—';
 const ns='http://www.w3.org/2000/svg';
 const metricNotes={
  spearman:'Spearman rho compares rankings using average ranks for tied scores. It measures ordering, not equality of score points.',
  pearson:'Pearson r measures linear association. Two scores can correlate strongly while differing systematically in level or scale.',
  ccc:'Lin concordance correlation (CCC) measures numerical agreement on the published 0–100 scales. Unlike correlation, it penalises differences in score level and spread. PCA percentile calibration affects this comparison.',
  kappa:'Quadratic-weighted Cohen kappa compares relative rank quintiles. Equal scores stay together using average ranks, so quintiles can differ in size. These are empirical groups, not housing-quality thresholds.',
  bottom_jaccard:'Bottom-decile Jaccard = intersection / union of homes (or areas) at or below each score\'s 10th percentile. Threshold ties are included: the groups can exceed 10%.',
  top_jaccard:'Top-decile Jaccard = intersection / union of homes (or areas) at or above each score\'s 90th percentile. Threshold ties are included: the groups can exceed 10%.'
 };
 let selectedA='41',selectedB='building';
 function selectedPair(a=selectedA,b=selectedB){return data.pairs.find(p=>p.scope===el('agreementScope').value&&((p.a===a&&p.b===b)||(p.a===b&&p.b===a)));}
 function heat(v){return v>=0?`hsl(175 38% ${97-61*v}%)`:`hsl(28 60% ${97+48*v}%)`;}
 function element(tag,attrs={},text='') {const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text)n.textContent=text;return n;}
 function addRow(table,values,header=false){const tr=document.createElement('tr');values.forEach((v,i)=>{const cell=document.createElement(header||i===0?'th':'td');cell.textContent=String(v);if(header)cell.scope='col';else if(i===0)cell.scope='row';tr.append(cell);});return tr;}
 function renderMatrix(){
  const metric=el('agreementMetric').value,scope=el('agreementScope').value,table=el('agreementMatrix');
  table.querySelector('thead').replaceChildren(addRow(table,['Score',...models.map(m=>m.short)],true));
  const body=table.querySelector('tbody');body.replaceChildren();
  for(const a of models){const tr=document.createElement('tr'),head=document.createElement('th');head.scope='row';head.textContent=a.short;tr.append(head);
   for(const b of models){const cell=document.createElement('td');const p=a.id===b.id?null:selectedPair(a.id,b.id),v=p?p[metric]:1;
    if(a.id===b.id){cell.textContent='1.000';cell.className='agreement-diagonal';cell.title='Self-comparison';}
    else{const button=document.createElement('button');button.type='button';button.textContent=coefficient(v);button.style.background=heat(v);button.style.color=Math.abs(v)>.57?'#fff':'#173744';
     button.setAttribute('aria-label',`${a.label} versus ${b.label}: ${metric} ${coefficient(v)}; n = ${count(p.n)}`);
     const chosen=(a.id===selectedA&&b.id===selectedB)||(a.id===selectedB&&b.id===selectedA);button.setAttribute('aria-pressed',String(chosen));button.title=`${a.label} / ${b.label} · n = ${count(p.n)}`;
     button.onclick=()=>{selectedA=a.id;selectedB=b.id;el('agreementA').value=selectedA;el('agreementB').value=selectedB;renderMatrix();renderPair();renderScatter();};cell.append(button);}
    tr.append(cell);
   }body.append(tr);
  }
  el('agreementMetricNote').textContent=metricNotes[metric];
  const summary=data.summary;
  el('agreementCohort').textContent=scope==='common_homes'?`${count(summary.common_homes)} identical latest sampled homes across all six scores (${pct(summary.common_home_coverage)} of ${count(summary.latest_homes)} latest homes). Overall rank concordance: Kendall W = ${coefficient(summary.kendall_w_common_homes)}.`:scope==='pairwise_homes'?'Each cell uses latest sampled homes with both scores available. Pair sizes differ; select a cell to see its denominator.':'Same-home area means: '+count(summary.eligible_authorities)+' authorities with at least 100 all-six-complete latest homes each. Equal weight per authority; '+count(summary.eligible_authority_homes)+' homes contribute. Kendall W = '+coefficient(summary.kendall_w_common_authorities)+'.';
 }
 function renderPair(){
  const p=selectedPair();if(!p)return;
  const reversed=selectedA!==p.a,scope=el('agreementScope').value;
  const aMean=reversed?p.mean_b:p.mean_a,bMean=reversed?p.mean_a:p.mean_b,bias=(reversed?-1:1)*p.mean_difference_b_minus_a;
  el('agreementPairTitle').textContent=short(selectedA)+' vs '+short(selectedB);
  el('agreementPairN').textContent='A: '+label(selectedA)+' · B: '+label(selectedB)+' · n = '+count(p.n)+(scope==='common_authorities'?' authorities':' latest sampled homes');
  const metrics=[['Spearman · Rankings',coefficient(p.spearman)],['Pearson · Linear relation',coefficient(p.pearson)],['Lin CCC · Score agreement',coefficient(p.ccc)],['Weighted quintile kappa',coefficient(p.kappa)],['Same rank quintile',pct(p.same_quintile)],['Bottom / top Jaccard',coefficient(p.bottom_jaccard)+' / '+coefficient(p.top_jaccard)],['Mean score · A / B',aMean.toFixed(2)+' / '+bMean.toFixed(2)],['Mean B − A',bias.toFixed(2)+' points'],['MAE / RMSE',p.mae.toFixed(2)+' / '+p.rmse.toFixed(2)+' points'],['Mean absolute rank gap',p.mean_abs_percentile_gap.toFixed(2)+' percentile points']];
  const dl=el('agreementPairMetrics');dl.replaceChildren();for(const [title,value] of metrics){const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=title;dd.textContent=value;div.append(dt,dd);dl.append(div);}
  const first=reversed?'b':'a',second=reversed?'a':'b';
  el('agreementTailNote').textContent='Ties retained. Actual bottom groups A / B: '+pct(p['bottom_share_'+first])+' / '+pct(p['bottom_share_'+second])+'; top groups: '+pct(p['top_share_'+first])+' / '+pct(p['top_share_'+second])+'. Threshold ties can make a decile larger than 10%.';
 }
 function renderScatter(){
  const svg=el('agreementScatter'),ranks=el('agreementScatterMode').value==='ranks',N=data.authorities.length;
  svg.replaceChildren(element('title',{},`${label(selectedA)} versus ${label(selectedB)}: ${ranks?'authority rank percentiles':'same-cohort authority mean scores'}`));
  const left=66,top=20,width=545,height=295,x=v=>left+width*v/100,y=v=>top+height*(1-v/100);
  for(const tick of [0,25,50,75,100]){
   svg.append(element('line',{x1:x(tick),y1:top,x2:x(tick),y2:top+height,stroke:'#e5ecee'}),element('line',{x1:left,y1:y(tick),x2:left+width,y2:y(tick),stroke:'#e5ecee'}));
   svg.append(element('text',{x:x(tick),y:top+height+20,'text-anchor':'middle'},String(tick)),element('text',{x:left-10,y:y(tick)+4,'text-anchor':'end'},String(tick)));
  }
  svg.append(element('line',{x1:x(0),y1:y(0),x2:x(100),y2:y(100),stroke:'#b57e55','stroke-dasharray':'5 5'}));
  for(const area of data.authorities){const ax=ranks?100*(N-area.ranks[selectedA])/(N-1):area.scores[selectedA],by=ranks?100*(N-area.ranks[selectedB])/(N-1):area.scores[selectedB];
   const point=element('circle',{cx:x(ax),cy:y(by),r:3.8,fill:'#277b83','fill-opacity':.65,tabindex:0,role:'img'});
   const text=area.name+' · '+count(area.n)+' common homes · A '+area.scores[selectedA].toFixed(2)+' (rank '+area.ranks[selectedA]+') · B '+area.scores[selectedB].toFixed(2)+' (rank '+area.ranks[selectedB]+')';
   point.append(element('title',{},text));point.setAttribute('aria-label',text);const show=()=>{el('agreementScatterDetail').textContent=text;};point.onpointerenter=show;point.onfocus=show;svg.append(point);
  }
  svg.append(element('text',{x:left+width/2,y:370,'text-anchor':'middle'},'A · '+short(selectedA)+(ranks?' · Rank percentile':' · Mean score')),
   element('text',{x:17,y:top+height/2,transform:`rotate(-90 17 ${top+height/2})`,'text-anchor':'middle'},'B · '+short(selectedB)+(ranks?' · Rank percentile':' · Mean score')));
  el('agreementScatterNote').textContent='Each point = one of '+N+' authorities, averaging identical all-six-complete homes (n ≥ 100). This plot always uses these area means, regardless of the matrix sample selector. Dashed line = equality. '+(ranks?'Higher percentiles mean higher CHQ ranks.':'Published 0–100 scales have different calibrations.');
  el('agreementScatterDetail').textContent='Hover or focus a point to inspect an authority.';
 }
 function renderFixedTables(){
  const coverage=el('agreementCoverageTable');coverage.querySelector('thead').replaceChildren(addRow(coverage,['Score','Latest homes scored','Availability','All-six common homes'],true));
  for(const m of models){const c=data.coverage.find(r=>r.model===m.id);coverage.querySelector('tbody').append(addRow(coverage,[m.label,count(c.latest_available),pct(c.latest_coverage),count(data.summary.common_homes)]));}
  const patterns=el('agreementPatternTable');patterns.querySelector('thead').replaceChildren(addRow(patterns,['Pattern','Common homes',...models.map(m=>m.short)],true));
  data.pattern_names.forEach((name,i)=>{const rows=data.pattern_distributions.filter(r=>r.cluster_id===i);patterns.querySelector('tbody').append(addRow(patterns,[name,count(rows[0].n),...models.map(m=>rows.find(r=>r.model===m.id).mean.toFixed(1))]));});
  patterns.querySelector('tbody').append(addRow(patterns,['Eta-squared · Association','—',...models.map(m=>data.pattern_associations.find(p=>p.model===m.id).eta_squared.toFixed(3))]));
 }
 for(const selectId of ['agreementA','agreementB'])for(const model of models){const option=document.createElement('option');option.value=model.id;option.textContent=model.label;el(selectId).append(option);}
 el('agreementA').value=selectedA;el('agreementB').value=selectedB;
 for(const id of ['agreementA','agreementB'])el(id).onchange=()=>{
  const a=el('agreementA').value,b=el('agreementB').value;
  if(a===b){if(id==='agreementA')el('agreementB').value=selectedA;else el('agreementA').value=selectedB;}
  selectedA=el('agreementA').value;selectedB=el('agreementB').value;renderMatrix();renderPair();renderScatter();
 };
 for(const id of ['agreementScope','agreementMetric'])el(id).onchange=()=>{renderMatrix();renderPair();};
 el('agreementScatterMode').onchange=renderScatter;
 const flats=data.common_cohort_coverage.find(r=>r.group_variable==='property_type'&&r.group==='Flat'),maisonettes=data.common_cohort_coverage.find(r=>r.group_variable==='property_type'&&r.group==='Maisonette');
 el('agreementCoverageNote').textContent='Common-cohort selection: '+pct(data.summary.common_home_coverage)+' of latest homes remain. All are report type 2; only '+pct(flats.common_coverage)+' of flats and '+pct(maisonettes.common_coverage)+' of maisonettes remain. Use Pairwise available homes and the coverage/subgroup downloads to check how this restriction affects results.';
 renderFixedTables();renderMatrix();renderPair();renderScatter();
})();
