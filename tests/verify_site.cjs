const {spawn}=require('node:child_process');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const assert=require('node:assert/strict');
const base=process.argv[2]||'http://127.0.0.1:8765';
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'chq-site-test-'));
const browser=spawn(process.env.CHROME_BIN||'/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome',['--headless','--no-sandbox','--disable-gpu','--remote-debugging-port=9238','--remote-allow-origins=*','--user-data-dir='+profile,'about:blank'],{stdio:'ignore'});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let ws,closeBrowser;
(async()=>{try{
 let tab;
 for(let i=0;i<100;i++){try{const r=await fetch('http://127.0.0.1:9238/json/new?'+encodeURIComponent(base),{method:'PUT'});tab=await r.json();break;}catch(e){await pause(100);}}
 if(!tab)throw Error('Could not start Chromium');
 ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 let id=0;const pending=new Map(),errors=[];
 ws.onmessage=ev=>{const r=JSON.parse(ev.data);if(r.id){const cb=pending.get(r.id);pending.delete(r.id);if(r.error)cb.reject(r.error);else cb.resolve(r.result);}else if(r.method==='Runtime.exceptionThrown')errors.push(r.params);};
 const call=(method,params={})=>new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params}));});
 closeBrowser=()=>call('Browser.close');
 await call('Runtime.enable');await call('Page.enable');await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
 await call('Page.reload');
 const ev=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 for(let i=0;i<100;i++){await pause(100);if(await ev(`document.getElementById('score')?.textContent==='62.52'`))break;}
 assert.equal(await ev(`document.getElementById('score').textContent`),'62.52');
 assert.equal(await ev(`document.querySelectorAll('#map path').length`),318);
 assert.equal(await ev(`document.getElementById('year').options.length`),14);
 assert.equal(await ev(`[...document.querySelectorAll('#map path')].filter(p=>p.getAttribute('fill')==='#dce2e8').length`),1);
 assert.equal(await ev(`document.getElementById('status').textContent.includes('4,368,473')`),true);
 await ev(`document.getElementById('areaSearch').value='Tower Hamlets';document.getElementById('searchForm').requestSubmit();true`);
 assert.equal(await ev(`document.getElementById('name').textContent`),'Tower Hamlets');
 assert.equal(await ev(`document.getElementById('score').textContent`),'75.88');
 await ev(`document.getElementById('year').value='2012';document.getElementById('year').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`document.getElementById('status').textContent.includes('102,988')`),true);
 await ev(`document.getElementById('year').value='all';document.getElementById('year').dispatchEvent(new Event('change'));document.querySelector('path[data-code="E09000030"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));true`);
 assert.equal(await ev(`document.getElementById('score').textContent`),'75.88');
 assert.equal(await ev(`document.querySelectorAll('#variables tbody tr').length`),41);
 assert.equal(await ev(`document.querySelectorAll('main > section').length`),3);
 assert.equal(await ev(`Array.from(document.body.textContent).some(c=>c.codePointAt(0)>=0x4e00&&c.codePointAt(0)<=0x9fff)`),false);
 const dictionary=await (await fetch(new URL('downloads/chq_41_variables.csv',base.endsWith('/')?base:base+'/'))).text();
 assert.equal(dictionary.trim().split('\n').length,42);
 for(const k of [5,10,18]){
  await ev(`document.getElementById('variant').value='${k}';document.getElementById('variant').dispatchEvent(new Event('change'));true`);
  assert.equal(await ev(`document.querySelectorAll('#variables tbody tr').length`),k);
  const expected={5:3572966,10:3206308,18:2978391}[k];
  assert.equal(await ev(`Object.values(rows()).reduce((s,r)=>s+r.n,0)`),expected);
  for(const view of ['coverage','baseline','score']){
   await ev(`document.getElementById('view').value='${view}';document.getElementById('view').dispatchEvent(new Event('change'));true`);
   assert.equal(await ev(`document.getElementById('score').textContent.includes('NaN')`),false);
  }
  await ev(`document.getElementById('year').value='2024';document.getElementById('year').dispatchEvent(new Event('change'));true`);
  assert.equal(await ev(`Object.values(rows()).every(r=>r.n<=r.total)`),true);
  await ev(`document.getElementById('year').value='all';document.getElementById('year').dispatchEvent(new Event('change'));true`);
 }
 // Six-attribute patterns: categories, denominators, prevalence and cohort controls.
 await ev(`document.getElementById('variant').value='patterns';document.getElementById('variant').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`document.getElementById('view').value`),'pattern');
 assert.equal(await ev(`document.querySelectorAll('#variables tbody tr').length`),4);
 assert.equal(await ev(`document.querySelectorAll('#variables thead th').length`),10);
 assert.equal(await ev(`Object.values(rows()).reduce((s,r)=>s+r.n,0)`),3978374);
 assert.equal(await ev(`Object.values(rows()).reduce((s,r)=>s+r.total,0)`),3978626);
 assert.equal(await ev(`BUILDING_CLUSTERS.summary.fit_entities_complete`),3978388);
 assert.equal(await ev(`Object.values(rows()).every(r=>r.counts.reduce((s,n)=>s+n,0)===r.n&&r.n<=r.total&&(!r.n||Math.abs(r.shares.reduce((s,n)=>s+n,0)-1)<1e-9))`),true);
 assert.equal(await ev(`document.getElementById('continuousLegend').hidden`),true);
 assert.equal(await ev(`document.querySelectorAll('#patternLegend > span').length`),4);
 assert.equal(await ev(`document.getElementById('patternBreakdown').hidden`),false);
 assert.equal(await ev(`document.getElementById('score').textContent`),await ev(`BUILDING_CLUSTERS.profiles[rows()['E09000030'].dominant].name`));
 assert.equal(await ev(`document.querySelector('path[data-code="E09000030"]').getAttribute('fill')`),await ev(`BUILDING_CLUSTERS.profiles[rows()['E09000030'].dominant].color`));
 assert.equal(await ev(`document.getElementById('dictionaryDownload').getAttribute('href')`),'downloads/chq_building_cluster_profiles.csv');
 for(const value of ['share0','share1','share2','share3','coverage','score']){
  await ev(`document.getElementById('view').value='${value}';document.getElementById('view').dispatchEvent(new Event('change'));true`);
  assert.equal(await ev(`document.getElementById('score').textContent`),await ev(`displayed(rows()['E09000030']).toFixed(2)`));
  assert.equal(await ev(`document.getElementById('continuousLegend').hidden`),false);
 }
 for(const year of ['2012','2024']){
  await ev(`document.getElementById('year').value='${year}';document.getElementById('year').dispatchEvent(new Event('change'));true`);
  assert.equal(await ev(`Object.values(rows()).every(r=>r.n<=r.total)`),true);
  assert.equal(await ev(`document.getElementById('status').textContent.includes('latest homes')`),true);
 }
 await ev(`document.getElementById('year').value='all';document.getElementById('year').dispatchEvent(new Event('change'));document.getElementById('view').value='pattern';document.getElementById('view').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`Object.values(rows()).every(r=>r.n===Object.entries(BUILDING_CLUSTERS.periods).filter(([y])=>y!=='all').reduce((s,[,data])=>s+(data[Object.keys(rows()).find(c=>rows()[c].name===r.name)]?.n||0),0))`),true);
 if(process.env.SCREENSHOT_DIR){fs.mkdirSync(process.env.SCREENSHOT_DIR,{recursive:true});const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(path.join(process.env.SCREENSHOT_DIR,'patterns-desktop.png'),Buffer.from(shot.data,'base64'));}
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 assert.equal(await ev(`document.documentElement.scrollWidth<=window.innerWidth`),true,'Pattern mobile horizontal overflow');
 if(process.env.SCREENSHOT_DIR){const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(path.join(process.env.SCREENSHOT_DIR,'patterns-mobile.png'),Buffer.from(shot.data,'base64'));}
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
 await ev(`document.getElementById('variant').value='building';document.getElementById('variant').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`document.getElementById('view').value`),'score');
 assert.equal(await ev(`document.querySelectorAll('#variables tbody tr').length`),6);
 assert.equal(await ev(`document.getElementById('patternBreakdown').hidden`),true);
 await ev(`document.getElementById('variant').value='pca41';document.getElementById('variant').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`document.querySelectorAll('#variables tbody tr').length`),41);
 assert.equal(await ev(`document.getElementById('variables-title').textContent.includes('PCA')`),true);
 await ev(`document.getElementById('variant').value='41';document.getElementById('variant').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`document.getElementById('score').textContent`),'75.88');
 const before=await ev(`document.getElementById('map').getAttribute('viewBox')`);
 await ev(`document.getElementById('plus').click();true`);
 assert.notEqual(await ev(`document.getElementById('map').getAttribute('viewBox')`),before);
 await ev(`document.getElementById('reset').click();document.getElementById('areaSearch').value='made-up-district';document.getElementById('searchForm').requestSubmit();true`);
 assert.equal(await ev(`document.getElementById('searchMessage').textContent.includes('not found')`),true);
 // CHQ agreement uses its own fixed common-home cohort, never the current map cohort.
 assert.equal(await ev(`CHQ_AGREEMENT.summary.common_homes`),2694335);
 assert.equal(await ev(`CHQ_AGREEMENT.summary.eligible_authorities`),314);
 assert.equal(await ev(`document.querySelectorAll('#agreementMatrix tbody tr').length`),6);
 assert.equal(await ev(`document.querySelectorAll('#agreementMatrix button').length`),30);
 assert.equal(await ev(`document.querySelectorAll('#agreementScatter circle').length`),314);
 assert.equal(await ev(`document.getElementById('agreementCoverageNote').textContent.includes('report type 2')`),true);
 assert.equal(await ev(`document.querySelectorAll('#agreementPatternTable tbody tr').length`),5);
 assert.equal(await ev(`document.querySelectorAll('#agreementCoverageTable tbody tr').length`),6);
 const agreementEntry=await ev(`CHQ_AGREEMENT.pairs.find(p=>p.scope==='common_homes'&&p.a==='41'&&p.b==='building').spearman`);
 assert.ok(Math.abs(agreementEntry-.9041898488)<1e-8);
 assert.equal(await ev(`document.querySelectorAll('#agreementMatrix tbody tr')[0].querySelectorAll('button')[3].textContent`),agreementEntry.toFixed(3));
 for(const metric of ['pearson','ccc','kappa','bottom_jaccard','top_jaccard','spearman']){
  await ev(`document.getElementById('agreementMetric').value='${metric}';document.getElementById('agreementMetric').dispatchEvent(new Event('change'));true`);
  assert.equal(await ev(`document.querySelectorAll('#agreementMatrix tbody tr')[0].querySelectorAll('button')[3].textContent`),await ev(`CHQ_AGREEMENT.pairs.find(p=>p.scope==='common_homes'&&p.a==='41'&&p.b==='building')['${metric}'].toFixed(3)`));
 }
 await ev(`document.getElementById('agreementScope').value='pairwise_homes';document.getElementById('agreementScope').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`document.getElementById('agreementPairN').textContent.includes('3,978,388')`),true);
 assert.equal(await ev(`document.querySelectorAll('#agreementMatrix tbody tr')[0].querySelectorAll('button')[3].textContent`),'0.936');
 await ev(`document.getElementById('agreementScope').value='common_authorities';document.getElementById('agreementScope').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`document.getElementById('agreementPairN').textContent.includes('314 authorities')`),true);
 assert.equal(await ev(`document.querySelectorAll('#agreementMatrix tbody tr')[0].querySelectorAll('button')[3].textContent`),'0.972');
 await ev(`document.getElementById('agreementScope').value='common_homes';document.getElementById('agreementScope').dispatchEvent(new Event('change'));document.querySelectorAll('#agreementMatrix tbody tr')[4].querySelectorAll('button')[0].click();true`);
 assert.equal(await ev(`document.getElementById('agreementA').value`),'building');
 assert.equal(await ev(`document.getElementById('agreementB').value`),'41');
 assert.equal(await ev(`[...document.querySelectorAll('#agreementPairMetrics > div')].find(row=>row.querySelector('dt').textContent==='Mean B − A').querySelector('dd').textContent`),'-2.48 points');
 await ev(`document.getElementById('agreementScatterMode').value='ranks';document.getElementById('agreementScatterMode').dispatchEvent(new Event('change'));document.querySelector('#agreementScatter circle').dispatchEvent(new Event('focus'));true`);
 assert.equal(await ev(`document.querySelectorAll('#agreementScatter circle').length`),314);
 assert.equal(await ev(`[...document.querySelectorAll('#agreementScatter circle')].every(c=>Number.isFinite(Number(c.getAttribute('cx')))&&Number.isFinite(Number(c.getAttribute('cy'))))`),true);
 assert.equal(await ev(`document.getElementById('agreementScatterDetail').textContent.includes('common homes')`),true);
 await ev(`document.getElementById('agreementA').value='41';document.getElementById('agreementA').dispatchEvent(new Event('change'));true`);
 assert.notEqual(await ev(`document.getElementById('agreementA').value`),await ev(`document.getElementById('agreementB').value`));
 await ev(`document.querySelectorAll('#agreementMatrix tbody tr')[0].querySelectorAll('button')[3].click();document.getElementById('agreementScatterMode').value='scores';document.getElementById('agreementScatterMode').dispatchEvent(new Event('change'));true`);
 if(process.env.SCREENSHOT_DIR){const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(path.join(process.env.SCREENSHOT_DIR,'agreement-desktop.png'),Buffer.from(shot.data,'base64'));}
 const resources=await ev(`JSON.stringify([...document.querySelectorAll('a[download],script[src],link[href]')].map(a=>a.href||a.src))`);
 for(const url of JSON.parse(resources)){const r=await fetch(url);assert.equal(r.status,200,url);}
 await ev(`document.getElementById('areaSearch').value='';document.getElementById('searchForm').requestSubmit();true`);
 assert.equal(await ev(`document.documentElement.scrollWidth<=window.innerWidth`),true);
 if(process.env.SCREENSHOT_DIR){fs.mkdirSync(process.env.SCREENSHOT_DIR,{recursive:true});const shot=await call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(process.env.SCREENSHOT_DIR,'desktop.png'),Buffer.from(shot.data,'base64'));}
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await pause(300);
 assert.equal(await ev(`document.documentElement.scrollWidth<=window.innerWidth`),true,'Mobile horizontal overflow');
 await ev(`document.querySelectorAll('#agreement .agreement-extra').forEach(d=>d.open=true);true`);
 assert.equal(await ev(`document.documentElement.scrollWidth<=window.innerWidth`),true,'Agreement expanded mobile overflow');
 if(process.env.SCREENSHOT_DIR){const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(path.join(process.env.SCREENSHOT_DIR,'mobile.png'),Buffer.from(shot.data,'base64'));}
 assert.equal(errors.length,0,JSON.stringify(errors));
 console.log(JSON.stringify({status:'passed',url:base,areas:318,years:14,search:true,keyboard_selection:true,year_controls:true,variable_table_rows:41,sections:3,candidate_variants:[5,10,18],building_patterns:4,pattern_share_views:4,pattern_latest_home_denominators:true,building_and_pca_regression:true,agreement_matrix:'6 scores, 3 cohorts, 6 metrics',agreement_pair_direction:true,agreement_authority_scatter:314,coverage_and_same_cohort_views:true,zoom:true,downloads:'all HTTP 200',mobile:'no horizontal overflow',runtime_errors:errors.length},null,2));
 }finally{
  if(closeBrowser)await Promise.race([closeBrowser().catch(()=>{}),pause(1000)]);
  if(ws)ws.close();browser.kill();
  await fs.promises.rm(profile,{recursive:true,force:true,maxRetries:20,retryDelay:100});
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
