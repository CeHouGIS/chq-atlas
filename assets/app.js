const $=id=>document.getElementById(id),svg=$('map'),paths=[...svg.querySelectorAll('path')];
const fmt=n=>n.toLocaleString('en-GB');
const base=[-18,-18,782.78,886];let box=[...base],selected=null,drag=null,moved=false;
function rows(){
 const period=$('year').value,variant=$('variant').value;
 if(variant==='building')return BUILDING_DATA[period]||{};
 if(variant==='pca41')return PCA41_DATA[period]||{};
 return Object.fromEntries(Object.entries(DATA[period]||{}).map(([code,r])=>{
  if(variant==='41')return [code,{...r,total:r.n,baseline:r.chq}];
  const c=CANDIDATES[period]?.[code]?.[variant]||{n:0,chq:null,coverage:0,baseline:null};
  return [code,{name:r.name,region:r.region,total:r.n,...c}];
 }));
}
function displayed(r){return $('view').value==='coverage'?100*r.coverage:$('view').value==='baseline'?r.baseline:r.chq;}
function formatScore(value){return Number.isFinite(value)?value.toFixed(2):'—';}
function details(code){
 let r=code?rows()[code]:null;
 if(!r){const rr=Object.values(rows()),n=rr.reduce((s,r)=>s+r.n,0),total=rr.reduce((s,r)=>s+r.total,0);r={name:'England & Wales',region:'Selected period · All mapped sales',n,total,chq:n?rr.reduce((s,r)=>s+r.n*(r.chq??0),0)/n:null,baseline:n?rr.reduce((s,r)=>s+r.n*(r.baseline??0),0)/n:null,coverage:$('variant').value==='41'?(n?rr.reduce((s,r)=>s+r.n*r.coverage,0)/n:0):n/total};}
 $('name').textContent=r.name;$('region').textContent=r.region;$('score').textContent=formatScore(displayed(r));$('scoreUnit').textContent=$('view').value==='coverage'?'%':'/ 100';$('count').textContent=fmt(r.n)+' / '+fmt(r.total);$('coverage').textContent=(r.coverage*100).toFixed(1)+'%';$('code').textContent=code||'—';
 $('coverageLabel').textContent=$('variant').value==='41'?'Variable completeness':$('variant').value==='pca41'?'Mean PCA input coverage':'Complete-score coverage';
 $('selectionNote').textContent=r.n===0?'No complete scores for this selection.':r.n<100?'Fewer than 100 scored transactions; interpret with caution.':'Sales-sample mean. Scores from different variable sets have different distributions.';
 for(const p of paths)p.classList.toggle('active',p.dataset.code===code);
}
function choose(code){selected=code;if(code&&!rows()[code]){selected=null;$('searchMessage').textContent='No records for this authority in the selected year.';}else $('searchMessage').textContent='';details(selected);}
function candidateRule(r,variant){
 if(variant==='41')return r.scoring_rule;
 const ranges={current_energy_efficiency:[24,88,false],energy_consumption_current:[44,643,true],open_fireplace_density:[0,.4,true],hot_water_cost_current_per_area:[.4789409155,6.116173913,true],lighting_cost_current_per_area:[.4761904762,1.519065239,true]};
 let rule=r.scoring_rule.replace(/ P1–P99 scale.*$/,'');
 if(ranges[r.variable]){const [lo,hi,reverse]=ranges[r.variable];rule+=' Discovery P1–P99 scale ['+lo+', '+hi+'], clipped to 0–1'+(reverse?'; reversed.':'.');}
 if(['walls_description','roof_description','floor_description','windows_description','mainheat_description','mainheatcont_description','hotwater_description','main_fuel'].includes(r.variable))rule+=' Category scores calibrated on discovery data only.';
 return rule;
}
function drawTable(){
 const variant=$('variant').value;
 const table=document.querySelector('#variables table'),thead=table.querySelector('thead'),tbody=table.querySelector('tbody');tbody.replaceChildren();
 if(variant==='pca41'){
  const model=PCA41_MODEL,byVar=Object.fromEntries(model.loadings.map(x=>[x.variable,x]));
  thead.innerHTML='<tr><th scope="col">#</th><th scope="col">Variable</th><th scope="col">Source field(s)</th><th scope="col">Direction</th><th scope="col">PC1 loading</th><th scope="col">PC2 loading</th><th scope="col">PC3 loading</th><th scope="col">PC4 loading</th></tr>';
  VARIABLES.forEach((r,i)=>{const l=byVar[r.variable],tr=document.createElement('tr');const vals=[String(i+1),r.label,r.source_fields.split(';').join(' · '),r.higher_chq_means,l.PC1.toFixed(3),l.PC2.toFixed(3),l.PC3.toFixed(3),l.PC4.toFixed(3)];vals.forEach((v,j)=>{const td=document.createElement(j===1?'th':'td');td.textContent=v;if(j===1){td.scope='row';const code=document.createElement('code');code.textContent=r.variable;td.append(code);}tr.append(td);});tbody.append(tr);});
  $('variables-title').textContent='2. PCA loading table · 41 variables';$('dictionaryDownload').href='downloads/chq_pca41_loadings.csv';$('tableNote').textContent='PCA loadings for the 41 current-state variables. Four retained PCs explain '+(100*model.cumulative).toFixed(1)+'% of standardized variance; loadings are signed and sample-dependent.';
 } else {
  thead.innerHTML='<tr><th scope="col">#</th><th scope="col">Variable</th><th scope="col">Source field(s)</th><th scope="col">Higher CHQ means</th><th scope="col">Scoring rule (0–1)</th><th scope="col">Missing / N.A.</th><th scope="col">Selection frequency</th></tr>';
  const chosen=variant==='41'?VARIABLES:variant==='building'?['walls_energy_eff','windows_energy_eff','mainheat_energy_eff','mainheatc_energy_eff','hot_water_energy_eff','lighting_energy_eff'].map(v=>VARIABLES.find(r=>r.variable===v)):SUBSETS[variant].map(v=>VARIABLES.find(r=>r.variable===v));
  chosen.forEach((r,i)=>{const tr=document.createElement('tr');const values=[String(i+1),r.label,r.source_fields.split(';').join(' · '),r.higher_chq_means,candidateRule(r,variant),Number(r.missing_pct)>0&&Number(r.missing_pct)<.01?'<0.01%':Number(r.missing_pct).toFixed(2)+'%',variant==='41'||variant==='building'?'—':Math.round((FREQUENCIES[variant]?.[r.variable]||0)*100)+'%'];values.forEach((v,j)=>{const td=document.createElement(j===1?'th':'td');td.textContent=v;if(j===1){td.scope='row';const code=document.createElement('code');code.textContent=r.variable;td.append(code);}tr.append(td);});tbody.append(tr);});
  $('variables-title').textContent='2. Variable attribute table · '+chosen.length;$('dictionaryDownload').href=variant==='41'?'downloads/chq_41_variables.csv':variant==='building'?'downloads/chq_building_only_dictionary.csv':'downloads/chq_'+variant+'_candidate_dictionary.csv';$('tableNote').textContent=(variant==='41'?'Baseline variables.':variant==='building'?'Building-only variables; equal weight 1/6 and complete records only.':'Candidate variables; equal weight 1/'+variant+' when all are available. Selection frequency: 100 geographically grouped re-fits, not climate importance.')+' Missing rates refer to the original full-sample 41-variable coding; candidate encodings were refitted on discovery data.';
 }
}
function draw(){
 const variant=$('variant').value;
 const baselineOption=$('view').querySelector('option[value="baseline"]');
 baselineOption.disabled=variant==='building'||variant==='pca41';
 if((variant==='building'||variant==='pca41')&&$('view').value==='baseline')$('view').value='score';
 let total=0,scored=0,shown=0;const rs=rows(),coverage=$('view').value==='coverage';
 for(const p of paths){const r=rs[p.dataset.code],value=r?displayed(r):null,hide=!r||!Number.isFinite(value)||(coverage?r.total<100:r.n<100);p.setAttribute('fill',hide?'#dce2e8':PALETTE[Math.round(Math.max(0,Math.min(1,coverage?value/100:(value-50)/40))*255)]);if(r){total+=r.total;scored+=r.n;if(!hide)shown++;}}
 $('status').textContent=fmt(scored)+' scored / '+fmt(total)+' records · '+shown+' areas coloured';
 $('legendLow').textContent=coverage?'0%':'50';$('legendHigh').textContent=coverage?'100%':'90';
 $('legendNote').textContent=coverage?(variant==='41'?'Mean available variables / 41.':variant==='building'?'Share of records with all six EPC variables available.':variant==='pca41'?'Mean input coverage across 41 variables.':'Share of transactions with all '+variant+' selected variables available.'):'Mean score (0–100). Fixed colour scale: 50–90. Grey: no score or fewer than 100 scored records.';
 $('variantNote').textContent=variant==='41'?'Baseline: available-variable mean of 41 scores. Fixed ONS 2024 boundaries.':variant==='pca41'?'41-variable PCA CHQ: standardized, median-imputed inputs; four PCs explain '+(100*PCA41_MODEL.cumulative).toFixed(1)+'% of variance. PC weights follow explained variance and the sign is aligned to the equal-weight baseline. Exploratory, not health-outcome validated.':variant==='building'?'Building-only CHQ: six equally weighted observed EPC building attributes; no outdoor climate exposure. Complete records only. It is a transparent building-attribute proxy, not a validated full climate-housing-quality outcome.':'Research candidate: fixed '+variant+'-variable mean, complete records only. No independent climate validation. '+(variant==='10'?'Full coverage 73.4%; flats 22.8%. Heating and lighting representatives are not fully stable.':variant==='5'?'Full coverage 81.8%; lower information retention and unstable representatives.':'Full coverage 68.2%; a broader information-retention comparison.')+' Use Coverage to inspect missingness; Same cohort compares the original baseline on these exact scored sales.';
 if(selected&&!rs[selected])selected=null;details(selected);drawTable();
}
$('gradient').style.background='linear-gradient(to right,'+PALETTE.filter((c,i)=>i%17===0||i===255).join(',')+')';
for(const [code,r] of Object.entries(DATA.all).sort((a,b)=>a[1].name.localeCompare(b[1].name))){const o=document.createElement('option');o.value=r.name;o.textContent=code;$('areaOptions').append(o);}
$('searchForm').onsubmit=e=>{e.preventDefault();const q=$('areaSearch').value.trim().toLowerCase();if(!q){choose(null);return;}const found=Object.entries(DATA.all).find(([c,r])=>c.toLowerCase()===q||r.name.toLowerCase()===q);if(found)choose(found[0]);else $('searchMessage').textContent='Authority not found. Choose a suggested name or enter a complete code.';};
for(const p of paths){p.setAttribute('tabindex','0');p.setAttribute('role','button');p.setAttribute('aria-label',DATA.all[p.dataset.code].name);p.addEventListener('click',()=>{if(!moved)choose(selected===p.dataset.code?null:p.dataset.code);});p.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(p.dataset.code);}});p.addEventListener('pointermove',e=>{const r=rows()[p.dataset.code];if(!r||drag)return;if(!selected)details(p.dataset.code);const tip=$('tooltip');tip.textContent=r.name+' · CHQ '+formatScore(displayed(r))+' · scored '+fmt(r.n)+' / '+fmt(r.total);tip.style.display='block';tip.style.left=Math.max(5,Math.min(e.clientX+12,window.innerWidth-270))+'px';tip.style.top=Math.max(5,Math.min(e.clientY+12,window.innerHeight-65))+'px';});p.addEventListener('pointerleave',()=>{$('tooltip').style.display='none';if(!selected)details(null);});}
function setBox(){svg.setAttribute('viewBox',box.join(' '));}
function zoom(f,cx=box[0]+box[2]/2,cy=box[1]+box[3]/2){const w=box[2]*f;if(w<base[2]/16||w>base[2]*1.6)return;box=[cx+(box[0]-cx)*f,cy+(box[1]-cy)*f,w,box[3]*f];setBox();}
svg.addEventListener('wheel',e=>{e.preventDefault();const q=new DOMPoint(e.clientX,e.clientY).matrixTransform(svg.getScreenCTM().inverse());zoom(e.deltaY<0?.85:1.18,q.x,q.y);},{passive:false});
svg.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY,...box];moved=false;});window.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag[0],dy=e.clientY-drag[1];if(Math.abs(dx)+Math.abs(dy)>4)moved=true;const units=1/svg.getScreenCTM().a;box=[drag[2]-dx*units,drag[3]-dy*units,drag[4],drag[5]];setBox();});window.addEventListener('pointerup',()=>{drag=null;setTimeout(()=>moved=false,0);});window.addEventListener('pointercancel',()=>{drag=null;});
$('plus').onclick=()=>zoom(.75);$('minus').onclick=()=>zoom(1.33);$('reset').onclick=()=>{box=[...base];setBox();$('areaSearch').value='';choose(null);};for(const id of ['year','variant','view'])$(id).onchange=draw;draw();
