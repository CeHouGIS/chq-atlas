const $=id=>document.getElementById(id),svg=$('map'),paths=[...svg.querySelectorAll('path')];
const fmt=n=>n.toLocaleString('en-GB');
const base=[-18,-18,782.78,886];let box=[...base],selected=null,drag=null,moved=false;
function rows(){return DATA[$('year').value]||{};}
function details(code){
 let r=code?rows()[code]:null;
 if(!r){const rr=Object.values(rows()),n=rr.reduce((s,r)=>s+r.n,0);r={name:'England & Wales',region:'Selected period · All mapped sales',n,chq:rr.reduce((s,r)=>s+r.n*r.chq,0)/n,coverage:rr.reduce((s,r)=>s+r.n*r.coverage,0)/n};}
 $('name').textContent=r.name;$('region').textContent=r.region;$('score').textContent=r.chq.toFixed(2);$('count').textContent=fmt(r.n);$('coverage').textContent=(r.coverage*100).toFixed(1)+'%';$('code').textContent=code||'—';
 $('selectionNote').textContent=r.n<100?'Fewer than 100 transactions; interpret this mean with caution.':'Transaction-sample mean; unadjusted for dwelling mix, year or missing-variable mix.';
 for(const p of paths)p.classList.toggle('active',p.dataset.code===code);
}
function choose(code){selected=code;if(code&&!rows()[code]){selected=null;$('searchMessage').textContent='No records for this authority in the selected year.';}else $('searchMessage').textContent='';details(selected);}
function draw(){let total=0,shown=0;const rs=rows();for(const p of paths){const r=rs[p.dataset.code],hide=!r||r.n<100;p.setAttribute('fill',hide?'#dce2e8':PALETTE[Math.round(Math.max(0,Math.min(1,(r.chq-50)/40))*255)]);if(r){total+=r.n;if(!hide)shown++;}}$('status').textContent=fmt(total)+' transactions · '+shown+' areas coloured';if(selected&&!rs[selected])selected=null;details(selected);}
$('gradient').style.background='linear-gradient(to right,'+PALETTE.filter((c,i)=>i%17===0||i===255).join(',')+')';
for(const [code,r] of Object.entries(DATA.all).sort((a,b)=>a[1].name.localeCompare(b[1].name))){const o=document.createElement('option');o.value=r.name;o.textContent=code;$('areaOptions').append(o);}
$('searchForm').onsubmit=e=>{e.preventDefault();const q=$('areaSearch').value.trim().toLowerCase();if(!q){choose(null);return;}const found=Object.entries(DATA.all).find(([c,r])=>c.toLowerCase()===q||r.name.toLowerCase()===q);if(found)choose(found[0]);else $('searchMessage').textContent='Authority not found. Choose a suggested name or enter a complete code.';};
for(const p of paths){p.setAttribute('tabindex','0');p.setAttribute('role','button');p.setAttribute('aria-label',DATA.all[p.dataset.code].name);p.addEventListener('click',()=>{if(!moved)choose(selected===p.dataset.code?null:p.dataset.code);});p.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(p.dataset.code);}});p.addEventListener('pointermove',e=>{const r=rows()[p.dataset.code];if(!r||drag)return;if(!selected)details(p.dataset.code);const tip=$('tooltip');tip.textContent=r.name+' · CHQ '+r.chq.toFixed(2)+' · n = '+fmt(r.n);tip.style.display='block';tip.style.left=Math.max(5,Math.min(e.clientX+12,window.innerWidth-270))+'px';tip.style.top=Math.max(5,Math.min(e.clientY+12,window.innerHeight-65))+'px';});p.addEventListener('pointerleave',()=>{$('tooltip').style.display='none';if(!selected)details(null);});}
function setBox(){svg.setAttribute('viewBox',box.join(' '));}
function zoom(f,cx=box[0]+box[2]/2,cy=box[1]+box[3]/2){const w=box[2]*f;if(w<base[2]/16||w>base[2]*1.6)return;box=[cx+(box[0]-cx)*f,cy+(box[1]-cy)*f,w,box[3]*f];setBox();}
svg.addEventListener('wheel',e=>{e.preventDefault();const q=new DOMPoint(e.clientX,e.clientY).matrixTransform(svg.getScreenCTM().inverse());zoom(e.deltaY<0?.85:1.18,q.x,q.y);},{passive:false});
svg.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY,...box];moved=false;});window.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag[0],dy=e.clientY-drag[1];if(Math.abs(dx)+Math.abs(dy)>4)moved=true;const units=1/svg.getScreenCTM().a;box=[drag[2]-dx*units,drag[3]-dy*units,drag[4],drag[5]];setBox();});window.addEventListener('pointerup',()=>{drag=null;setTimeout(()=>moved=false,0);});window.addEventListener('pointercancel',()=>{drag=null;});
$('plus').onclick=()=>zoom(.75);$('minus').onclick=()=>zoom(1.33);$('reset').onclick=()=>{box=[...base];setBox();$('areaSearch').value='';choose(null);};$('year').onchange=draw;draw();
