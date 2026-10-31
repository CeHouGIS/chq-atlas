(() => {
 'use strict';
 const data=BUILDING_PCA2,el=id=>document.getElementById(id),canvas=el('pcaSpaceCanvas'),axes=el('pcaSpaceAxes'),ctx=canvas.getContext('2d');
 const W=960,H=610,L=80,T=30,PW=830,PH=490,ns='http://www.w3.org/2000/svg';
 const fmt=n=>n.toLocaleString('en-GB'),pct=n=>(100*n).toFixed(2)+'%';
 const [xmin,xmax,ymin,ymax]=data.bounds,spanX=xmax-xmin+.12,spanY=ymax-ymin+.12,unit=Math.min(PW/spanX,PH/spanY);
 const centerX=(xmin+xmax)/2,centerY=(ymin+ymax)/2;
 const X=v=>L+PW/2+(v-centerX)*unit,Y=v=>T+PH/2-(v-centerY)*unit;
 const clusters=data.clusters;
 let selected=null,hits=[],hover=null;
 const svgNode=(tag,attrs={},text='')=>{const node=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))node.setAttribute(k,v);if(text)node.textContent=text;return node;};
 function visible(c){return selected===null||selected===c;}
 function drawAxes(){
  axes.replaceChildren();
  for(let v=Math.ceil((centerX-PW/2/unit)*4)/4;v<=centerX+PW/2/unit;v+=.25){
   axes.append(svgNode('line',{x1:X(v),y1:T,x2:X(v),y2:T+PH,stroke:Math.abs(v)<1e-8?'#b9c8cc':'#edf2f3'}));
   axes.append(svgNode('text',{x:X(v),y:T+PH+23,'text-anchor':'middle'},v.toFixed(2)));
  }
  for(let v=Math.ceil((centerY-PH/2/unit)*4)/4;v<=centerY+PH/2/unit;v+=.25){
   axes.append(svgNode('line',{x1:L,y1:Y(v),x2:L+PW,y2:Y(v),stroke:Math.abs(v)<1e-8?'#b9c8cc':'#edf2f3'}));
   axes.append(svgNode('text',{x:L-10,y:Y(v)+4,'text-anchor':'end'},v.toFixed(2)));
  }
  axes.append(svgNode('rect',{x:L,y:T,width:PW,height:PH,fill:'none',stroke:'#d3dfe2'}));
  axes.append(svgNode('text',{x:L+PW/2,y:580,'text-anchor':'middle',class:'pca-axis-title'},'PC1 · '+pct(data.summary.variance[0])+' explained variance'));
  axes.append(svgNode('text',{x:20,y:T+PH/2,transform:`rotate(-90 20 ${T+PH/2})`,'text-anchor':'middle',class:'pca-axis-title'},'PC2 · '+pct(data.summary.variance[1])+' explained variance'));
  for(const c of clusters.filter(c=>visible(c.cluster_id))){
   const x=X(c.pc1),y=Y(c.pc2),g=svgNode('g',{tabindex:0,role:'button','aria-label':`Pattern ${c.cluster_id+1} center: ${c.name}`,class:'pca-centroid'});
   g.append(svgNode('path',{d:`M${x-6},${y-6} L${x+6},${y+6} M${x-6},${y+6} L${x+6},${y-6}`,stroke:'#fff','stroke-width':7}),svgNode('path',{d:`M${x-6},${y-6} L${x+6},${y+6} M${x-6},${y+6} L${x+6},${y-6}`,stroke:c.color,'stroke-width':4}));
   g.append(svgNode('text',{x:x+11,y:y-9,fill:c.color,class:'pca-centroid-label'},String(c.cluster_id+1)));
   const show=()=>detail(c.name,`${fmt(c.n)} latest homes (${(100*c.share).toFixed(1)}% of the full cohort). Projected cluster mean: PC1 ${c.pc1.toFixed(3)}, PC2 ${c.pc2.toFixed(3)}.`,[]);
   g.onfocus=show;g.onclick=show;g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show();}};axes.append(g);
  }
 }
 function detail(title,text,values){
  el('pcaSpaceDetailTitle').textContent=title;el('pcaSpaceDetail').textContent=text;
  const dl=el('pcaSpaceDetailValues');dl.replaceChildren();
  for(const [label,value] of values){const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;div.append(dt,dd);dl.append(div);}
 }
 function draw(){
  const dpr=Math.min(window.devicePixelRatio||1,2),width=Math.max(320,canvas.clientWidth),height=width*H/W;
  canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(canvas.width/W,0,0,canvas.height/H,0,0);ctx.clearRect(0,0,W,H);hits=[];hover=null;
  const density=el('pcaSpaceMode').value==='density',shown=data.profiles.filter(p=>visible(p[2])),n=shown.reduce((sum,p)=>sum+p[3],0);
  canvas.dataset.visibleProfiles=String(shown.length);canvas.dataset.visibleHomes=String(n);canvas.dataset.mode=density?'density':'profiles';
  if(density){
   const bins=data.bins.map(b=>{const counts=b.counts.map((v,i)=>visible(i)?v:0);return {...b,counts,n:counts.reduce((s,v)=>s+v,0)};}).filter(b=>b.n>0),max=Math.max(...bins.map(b=>b.n));
   for(const b of bins){const dominant=b.counts.indexOf(Math.max(...b.counts)),alpha=.15+.85*Math.log1p(b.n)/Math.log1p(max);ctx.globalAlpha=alpha;ctx.fillStyle=clusters[dominant].color;const w=data.cell_width*unit,h=data.cell_height*unit;ctx.fillRect(X(b.x)-w/2,Y(b.y)-h/2,w+.2,h+.2);hits.push({x:X(b.x),y:Y(b.y),radius:Math.max(w,h)/2,type:'bin',b});}
   el('pcaSpaceDisplayNote').textContent=`Exact home-frequency density: ${fmt(n)} homes in ${fmt(bins.length)} occupied cells. Darker cells contain more homes (log count intensity, rescaled after filtering). Colour = plurality pattern within a cell; cell mixtures are shown on hover. Crosses = cluster means.`;
  } else {
   const max=Math.max(...data.profiles.map(p=>p[3]));
   for(const p of [...shown].sort((a,b)=>b[3]-a[3])){const radius=1+3.4*Math.sqrt(Math.log1p(p[3])/Math.log1p(max));ctx.beginPath();ctx.fillStyle=clusters[p[2]].color;ctx.globalAlpha=.42;ctx.arc(X(p[0]),Y(p[1]),radius,0,Math.PI*2);ctx.fill();hits.push({x:X(p[0]),y:Y(p[1]),radius,type:'profile',p});}
   el('pcaSpaceDisplayNote').textContent=`All ${fmt(shown.length)} distinct six-rating profiles representing ${fmt(n)} latest homes. One dot can represent many homes; marker area increases with log(1 + home count). No random sampling or jitter. Coincident / nearby points can overlap; use Home density to inspect frequency.`;
  }
  ctx.globalAlpha=1;drawAxes();
  for(const button of el('pcaSpaceLegend').querySelectorAll('button'))button.setAttribute('aria-pressed',String(Number(button.dataset.cluster)===selected));
  detail(selected===null?'Explore the distribution':clusters[selected].name,'Hover or tap the plot to inspect profiles or density cells. Select a pattern to view it separately; axis limits stay fixed.',[]);
 }
 function inspect(event){
  const rect=canvas.getBoundingClientRect(),x=(event.clientX-rect.left)/rect.width*W,y=(event.clientY-rect.top)/rect.height*H;
  let nearest=null,best=Infinity;
  for(const hit of hits){const d=Math.hypot(hit.x-x,hit.y-y);if(d<best&&d<Math.max(hit.radius+2,9)){nearest=hit;best=d;}}
  if(!nearest||nearest===hover)return;hover=nearest;
  if(nearest.type==='profile'){const p=nearest.p;detail(clusters[p[2]].name,`${fmt(p[3])} latest homes share this exact six-attribute profile. PC1 ${p[0].toFixed(3)} · PC2 ${p[1].toFixed(3)}. Ratings below use a 0–100 scale.`,data.labels.map((label,i)=>[label,(p[4+i]*100).toFixed(0)]));}
  else{const b=nearest.b;detail('Home density cell',`${fmt(b.n)} latest homes in this cell. Centre: PC1 ${b.x.toFixed(3)} · PC2 ${b.y.toFixed(3)}.`,clusters.filter(c=>visible(c.cluster_id)).map(c=>[c.name,fmt(b.counts[c.cluster_id])+' · '+(100*b.counts[c.cluster_id]/b.n).toFixed(1)+'%']));}
 }
 for(const c of clusters){const button=document.createElement('button'),swatch=document.createElement('i');button.type='button';button.dataset.cluster=c.cluster_id;swatch.style.background=c.color;button.append(swatch,document.createTextNode(`${c.cluster_id+1}. ${c.name} (${(100*c.share).toFixed(1)}%)`));button.onclick=()=>{selected=selected===c.cluster_id?null:c.cluster_id;draw();};el('pcaSpaceLegend').append(button);}
 for(const row of data.loadings){const tr=document.createElement('tr');[row.label,...['PC1_coefficient','PC2_coefficient','PC1_correlation_loading','PC2_correlation_loading'].map(k=>row[k].toFixed(3))].forEach((v,i)=>{const cell=document.createElement(i===0?'th':'td');cell.textContent=v;if(i===0)cell.scope='row';tr.append(cell);});el('pcaSpaceLoadings').querySelector('tbody').append(tr);}
 el('pcaSpaceSummary').textContent=`${fmt(data.summary.n_homes)} complete latest sampled homes, represented by all ${fmt(data.summary.n_profiles)} observed rating profiles. PC1 explains ${pct(data.summary.variance[0])}; PC2 ${pct(data.summary.variance[1])}. Together: ${pct(data.summary.retained)} of six-attribute variance. Centred original-scale PCA, matching the clustering metric.`;
 canvas.onpointermove=inspect;canvas.onclick=inspect;
 el('pcaSpaceMode').onchange=draw;el('pcaSpaceReset').onclick=()=>{selected=null;draw();};
 new ResizeObserver(()=>draw()).observe(canvas.parentElement);draw();
})();
