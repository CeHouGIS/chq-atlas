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
 assert.equal(await ev(`document.querySelectorAll('main > section').length`),2);
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
 await ev(`document.getElementById('variant').value='41';document.getElementById('variant').dispatchEvent(new Event('change'));true`);
 assert.equal(await ev(`document.getElementById('score').textContent`),'75.88');
 const before=await ev(`document.getElementById('map').getAttribute('viewBox')`);
 await ev(`document.getElementById('plus').click();true`);
 assert.notEqual(await ev(`document.getElementById('map').getAttribute('viewBox')`),before);
 await ev(`document.getElementById('reset').click();document.getElementById('areaSearch').value='made-up-district';document.getElementById('searchForm').requestSubmit();true`);
 assert.equal(await ev(`document.getElementById('searchMessage').textContent.includes('not found')`),true);
 const resources=await ev(`JSON.stringify([...document.querySelectorAll('a[download],script[src],link[href]')].map(a=>a.href||a.src))`);
 for(const url of JSON.parse(resources)){const r=await fetch(url);assert.equal(r.status,200,url);}
 await ev(`document.getElementById('areaSearch').value='';document.getElementById('searchForm').requestSubmit();true`);
 assert.equal(await ev(`document.documentElement.scrollWidth<=window.innerWidth`),true);
 if(process.env.SCREENSHOT_DIR){fs.mkdirSync(process.env.SCREENSHOT_DIR,{recursive:true});const shot=await call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(process.env.SCREENSHOT_DIR,'desktop.png'),Buffer.from(shot.data,'base64'));}
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await pause(300);
 assert.equal(await ev(`document.documentElement.scrollWidth<=window.innerWidth`),true,'Mobile horizontal overflow');
 if(process.env.SCREENSHOT_DIR){const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(path.join(process.env.SCREENSHOT_DIR,'mobile.png'),Buffer.from(shot.data,'base64'));}
 assert.equal(errors.length,0,JSON.stringify(errors));
 console.log(JSON.stringify({status:'passed',url:base,areas:318,years:14,search:true,keyboard_selection:true,year_controls:true,variable_table_rows:41,sections:2,candidate_variants:[5,10,18],coverage_and_same_cohort_views:true,zoom:true,downloads:'all HTTP 200',mobile:'no horizontal overflow',runtime_errors:errors.length},null,2));
 }finally{
  if(closeBrowser)await Promise.race([closeBrowser().catch(()=>{}),pause(1000)]);
  if(ws)ws.close();browser.kill();
  await fs.promises.rm(profile,{recursive:true,force:true,maxRetries:20,retryDelay:100});
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
