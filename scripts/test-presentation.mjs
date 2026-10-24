// Read-only acceptance checks for the five-slide presentation. Never calls app/AI APIs.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir,readFile,writeFile,readdir,rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(path.join(root,'frontend/package.json'));
const {chromium,expect}=require('@playwright/test');
const base=process.env.PRESENTATION_URL||'http://127.0.0.1:4174';
const output=path.join(root,'artifacts/presentation_qa');
await mkdir(output,{recursive:true});
for(const file of await readdir(output))if(/^(desktop|mobile)_/.test(file))await rm(path.join(output,file));
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const context=await browser.newContext({viewport:{width:1600,height:1000}});
const page=await context.newPage();
const errors=[],failedRequests=[],forbiddenRequests=[],checks=[],desktopFit=[],readability=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
page.on('requestfailed',r=>{if(!r.failure()?.errorText?.includes('ERR_ABORTED'))failedRequests.push({url:r.url(),error:r.failure()?.errorText});});
page.on('request',r=>{if(!['GET','HEAD'].includes(r.method())||new URL(r.url()).pathname.includes('/api/'))forbiddenRequests.push({method:r.method(),url:r.url()});});
const slideIds=['intro','problem','solution','explore','demo'];
const active=()=>page.locator('[data-slide].is-active');
const settled=()=>active().evaluate(e=>Promise.all(e.getAnimations().map(a=>a.finished)));
const visit=async id=>{await page.evaluate(hash=>{location.hash=hash;},id);await expect(active()).toHaveAttribute('id',id);await settled();};
const loaded=async selector=>{await expect.poll(()=>page.locator(selector).evaluate(i=>i.complete&&i.naturalWidth>0)).toBeTruthy();};
const overflow=async label=>{const v=await page.evaluate(()=>({width:innerWidth,html:document.documentElement.scrollWidth,body:document.body.scrollWidth}));assert.ok(v.html<=v.width+1&&v.body<=v.width+1,label+' '+JSON.stringify(v));};
const check=async(name,fn)=>{await fn();checks.push(name);console.log('PASS',name);};
let complete=false;
try{
 await page.goto(base+'/?qa='+Date.now()+'#intro',{waitUntil:'networkidle'});
 await check('Five slides: arrow/hash navigation, overview jump, notes and fullscreen',async()=>{
  await expect(page.locator('[data-slide]')).toHaveCount(5);
  await expect(page.locator('[data-action="prev"]')).toBeDisabled();
  for(const [i,id]of slideIds.entries()){
   if(i)await page.keyboard.press('ArrowRight');await expect(active()).toHaveAttribute('id',id);
   await expect(page).toHaveURL(new RegExp('#'+id+'$'));await expect(page.locator('#chapter-counter')).toHaveText(String(i+1).padStart(2,'0')+' / 05');
  }
  await expect(page.locator('[data-action="next"]')).toBeDisabled();
  await page.keyboard.press('ArrowLeft');await expect(active()).toHaveAttribute('id','explore');
  await page.reload();await expect(active()).toHaveAttribute('id','explore');
  await page.locator('[data-action="overview"]').click();await expect(page.locator('#overview-dialog')).toBeVisible();
  await expect(page.locator('#overview-grid [data-slide-link]')).toHaveCount(5);
  await page.locator('#overview-grid [data-slide-link="2"]').click();await expect(active()).toHaveAttribute('id','solution');
  await expect(page.locator('#overview-dialog')).not.toBeVisible();
  await page.keyboard.press('n');await expect(page.locator('#notes-panel')).toBeVisible();await expect(page.locator('#notes-copy')).not.toHaveText('');
  await page.keyboard.press('n');await expect(page.locator('#notes-panel')).not.toBeVisible();
  await expect(page.locator('[data-action="fullscreen"]')).toBeVisible();await page.locator('[data-action="fullscreen"]').click();
  await expect.poll(()=>page.evaluate(()=>!!document.fullscreenElement)).toBeTruthy();await page.evaluate(()=>document.exitFullscreen());
 });
 await check('Four plain workflow steps, optional genuine Gemma image and source scope',async()=>{
  await visit('solution');const titles=[];
  for(let i=0;i<4;i++){await page.locator(`[data-step="${i}"]`).click();await expect(page.locator(`[data-step="${i}"]`)).toHaveAttribute('aria-selected','true');titles.push(await page.locator('#step-title').innerText());}
  assert.equal(new Set(titles).size,4);
  await page.locator('[data-step="0"]').click();
  await page.locator('#solution [data-zoom="assets/gemma_extraction.png"]').click();await expect(page.locator('#image-dialog')).toBeVisible();await loaded('#lightbox-image');
  await expect(page.locator('#lightbox-image')).toHaveAttribute('src','assets/gemma_extraction.png');await page.keyboard.press('Escape');
  await visit('explore');await page.locator('#explore [data-action="sources"]').click();await expect(page.locator('#sources-dialog')).toBeVisible();
  await expect(page.locator('#sources-dialog')).toContainText('gemma-4-26b-a4b-it');await expect(page.locator('#sources-dialog')).toContainText('429');
  await page.locator('#sources-dialog [data-zoom="assets/gemma_investigation.png"]').click();await loaded('#lightbox-image');await expect(page.locator('#lightbox-image')).toHaveAttribute('src','assets/gemma_investigation.png');
  await page.keyboard.press('Escape');await expect(page.locator('#sources-dialog')).toBeVisible();await page.getByRole('button',{name:'Close sources',exact:true}).click();
 });
 await check('Both configured plant cases: source design, graph and 3D with correct equipment',async()=>{
  await visit('explore');
  await expect(page.locator('[data-case="lowerfox"]')).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('#case-image')).toHaveAttribute('src','assets/lowerfox_3d.png');
  for(const id of ['atlas','lowerfox']){
   await page.locator(`[data-case="${id}"]`).click();await expect(page.locator(`[data-case="${id}"]`)).toHaveAttribute('aria-pressed','true');
   await expect(page.locator('#case-equipment')).toContainText(id==='atlas'?'2 pumps':'3 pumps');
   for(const view of ['design','graph','3d']){await page.locator(`[data-view="${view}"]`).click();await expect(page.locator('#case-image')).toHaveAttribute('src',`assets/${id}_${view}.png`);await loaded('#case-image');}
  }
 });
 await check('Screenshot detail: actual image, zoom/reset, close button and Escape',async()=>{
  await page.locator('#case-image-button').click();await expect(page.locator('#image-dialog')).toBeVisible();await loaded('#lightbox-image');
  await expect(page.locator('#lightbox-image')).toHaveAttribute('src','assets/lowerfox_3d.png');
  const before=await page.locator('#zoom-reset').innerText();await page.locator('[data-image-zoom="in"]').click();await expect(page.locator('#zoom-reset')).not.toHaveText(before);
  await page.locator('[data-image-zoom="reset"]').click();await expect(page.locator('#zoom-reset')).toHaveText(before);
  await page.getByRole('button',{name:'Close screenshot',exact:true}).click();await expect(page.locator('#image-dialog')).not.toBeVisible();
  await page.locator('#case-image-button').click();await page.keyboard.press('Escape');await expect(page.locator('#image-dialog')).not.toBeVisible();
 });
 await check('Actual 89.8-second product video loads, plays and seeks through both chapters',async()=>{
  await visit('demo');const video=page.locator('#demo-video');
  await expect.poll(()=>video.evaluate(v=>Number.isFinite(v.duration)?v.duration:0),{timeout:20000}).toBeGreaterThan(89);
  assert.ok(await video.evaluate(v=>v.duration)<91);
  await page.locator('[data-chapter="33.24"]').click();await expect.poll(()=>video.evaluate(v=>!v.paused&&v.currentTime>33.4)).toBeTruthy();
  await video.evaluate(v=>{v.pause();v.currentTime=70;});await expect.poll(()=>video.evaluate(v=>v.seeking)).toBeFalsy();assert.ok(Math.abs(await video.evaluate(v=>v.currentTime)-70)<.2);
  await page.locator('[data-chapter="0"]').click();assert.ok(await video.evaluate(v=>v.currentTime)<2);
  // The real recording begins at a fresh blank browser tab; retain a decoded
  // product frame for the subsequent visual audit rather than pausing at t=0.
  await expect.poll(()=>video.evaluate(v=>v.currentTime),{timeout:10000}).toBeGreaterThan(4);
  await video.evaluate(v=>v.pause());
  await expect(page.locator('.video-note')).toContainText('No AI requests');
 });
 await check('White theme, strong main-text contrast, all five desktop slides fit vertically',async()=>{
  const bg=await page.evaluate(()=>getComputedStyle(document.body).backgroundColor);assert.equal(bg,'rgb(252, 252, 253)');
  for(const [i,id]of slideIds.entries()){
   await visit(id);await overflow('desktop '+id);
   for(const img of await active().locator('img').all())await expect.poll(()=>img.evaluate(e=>e.complete&&e.naturalWidth>0)).toBeTruthy();
   const fit=await active().evaluate(el=>{
    const footer=document.querySelector('.deck-footer').getBoundingClientRect().top;
    const items=[...el.querySelectorAll('h1,h2,h3,p,button,img,.case-equipment')].filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden').map(e=>({tag:e.tagName,id:e.id,text:(e.innerText||'').slice(0,55),top:e.getBoundingClientRect().top,bottom:e.getBoundingClientRect().bottom}));
    return {id:el.id,footer,overflow:items.filter(r=>r.bottom>footer-3||r.top<85)};
   });desktopFit.push(fit);assert.deepEqual(fit.overflow,[],id+' desktop clipping: '+JSON.stringify(fit.overflow));
   const contrast=await active().evaluate(el=>{
    function lum(rgb){return rgb.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((v,c,i)=>v+c*[.2126,.7152,.0722][i],0);}
    const bg=lum([252,252,253]);
    return [...el.querySelectorAll('h1,h2,.lead,.subtitle,.question-line h3,.question-line p,.case-story>p,.pipeline-step strong,.solution-detail h3,.solution-detail>p')].filter(e=>e.getClientRects().length).map(e=>{
     const c=getComputedStyle(e),fg=lum(c.color.match(/[\d.]+/g).map(Number)),ratio=(Math.max(bg,fg)+.05)/(Math.min(bg,fg)+.05);
     return {text:e.textContent.slice(0,55),size:parseFloat(c.fontSize),ratio:Number(ratio.toFixed(2))};
    });
   });readability.push({id,text:contrast});for(const item of contrast){assert.ok(item.ratio>=4.5,id+' low main contrast '+JSON.stringify(item));assert.ok(item.size>=18,id+' main narrative too small '+JSON.stringify(item));}
   await page.screenshot({path:path.join(output,`desktop_${String(i+1).padStart(2,'0')}_${id}.png`),fullPage:true});
  }
 });
 await check('All original evidence assets match provenance and all fourteen images decode',async()=>{
  const provenance=await(await context.request.get(base+'/assets/provenance.json')).json();assert.equal(provenance.assets.length,15);
  for(const asset of provenance.assets){const bytes=await readFile(path.join(root,'presentation/assets',asset.file));assert.equal(createHash('sha256').update(bytes).digest('hex'),asset.sha256,asset.file);assert.deepEqual(bytes,await readFile(path.join(root,asset.source)),asset.file+' equals original evidence');}
  const images=provenance.assets.filter(a=>a.file.endsWith('.png')).map(a=>'assets/'+a.file);
  const results=await page.evaluate(paths=>Promise.all(paths.map(src=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve({src,width:i.naturalWidth});i.onerror=()=>resolve({src,width:0});i.src=src;}))),images);
  assert.ok(results.every(i=>i.width>0));
 });
 await check('Mobile 390×844: five slides and image/overview dialogs have no horizontal overflow',async()=>{
  await page.setViewportSize({width:390,height:844});
  for(const [i,id]of slideIds.entries()){await visit(id);await overflow('mobile '+id);await page.screenshot({path:path.join(output,`mobile_${String(i+1).padStart(2,'0')}_${id}.png`),fullPage:true});}
  await visit('explore');await page.locator('[data-case="atlas"]').click();await page.locator('[data-view="graph"]').click();await loaded('#case-image');await overflow('mobile explorer');
  await page.locator('#case-image-button').click();await expect(page.locator('#image-dialog')).toBeVisible();await overflow('mobile screenshot');await page.keyboard.press('Escape');
  await page.locator('[data-action="overview"]').click();await expect(page.locator('#overview-dialog')).toBeVisible();await overflow('mobile overview');await page.keyboard.press('Escape');
 });
 await check('Print reveals all five slides and hides interactive navigation',async()=>{
  await page.setViewportSize({width:1600,height:1000});await page.emulateMedia({media:'print'});
  for(const id of slideIds)await expect(page.locator('#'+id)).toBeVisible();await expect(page.locator('.masthead')).not.toBeVisible();await expect(page.locator('.deck-footer')).not.toBeVisible();await page.emulateMedia({media:'screen'});
 });
 assert.deepEqual(forbiddenRequests,[],'No app or AI API requests');assert.deepEqual(failedRequests,[],'No missing resources');assert.deepEqual(errors,[],'No browser errors');complete=true;
}finally{
 await writeFile(path.join(output,'results.json'),JSON.stringify({tested_at:new Date().toISOString(),url:base,slides:5,complete,checks,desktopFit,readability,errors,failedRequests,forbiddenRequests,viewports:['1600x1000','390x844'],live_ai:false},null,2)+'\n');
 await context.close();await browser.close();
}
console.log(`PASS: ${checks.length} five-slide presentation acceptance groups; zero AI/API requests.`);
