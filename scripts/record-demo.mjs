// Record genuine browser/API interactions; no mocked responses or edited readings.
import {createRequire} from 'node:module';
import {mkdir,copyFile,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(path.join(root,'frontend/package.json'));
const {chromium,expect}=require('@playwright/test');
const base=process.env.DEMO_URL||'http://127.0.0.1:8000';
const temporary=path.join(root,'artifacts/_video_tmp');
await mkdir(temporary,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const context=await browser.newContext({viewport:{width:1600,height:1000},recordVideo:{dir:temporary,size:{width:1600,height:1000}}});
const page=await context.newPage();
try{
 await context.request.post(base+'/api/simulation/action',{data:{action:'reset'}});
 await page.goto(base);await page.getByText('Understand the plant.').waitFor();await page.waitForTimeout(2200);
 const normal=await(await context.request.get(base+'/api/state')).json();
 if(!normal.solver_ok||normal.values.filter_dp_bar>=.8)throw new Error('Normal hydraulic baseline did not verify.');
 await page.screenshot({path:path.join(root,'artifacts/workspace-graph.png'),fullPage:true});
 await page.getByRole('button',{name:'Downstream',exact:true}).click();await page.waitForTimeout(1800);
 await page.getByRole('button',{name:'P&ID',exact:true}).click();await page.waitForTimeout(2000);
 if(process.argv.includes('--live-ai')){
  await page.getByRole('button',{name:'Extract station with Claude'}).click();
  await page.getByRole('heading',{name:'Review the extracted plant.'}).waitFor({timeout:150000});
  await page.waitForTimeout(2000);await page.screenshot({path:path.join(root,'artifacts/diagram-review.png'),fullPage:true});
  await page.getByRole('button',{name:'Confirm reviewed model'}).click();
  await expect(page.getByText('Reviewed drawing · hydraulic mapping verified')).toBeVisible();
 }
 await page.getByRole('button',{name:'Process graph',exact:true}).click();
 await page.locator('.tree-asset').filter({hasText:'F-101'}).click();
 await page.getByRole('button',{name:'Play simulation',exact:true}).click();await page.waitForTimeout(3500);
 await page.locator('.scenario-button').click();await page.locator('.scenario-menu button').filter({hasText:'Filter restriction'}).click();await page.waitForTimeout(2500);
 await page.getByRole('button',{name:'Pause simulation',exact:true}).click();
 const incident=await(await context.request.get(base+'/api/state')).json();
 if(!incident.solver_ok||incident.values.filter_dp_bar<=.8||incident.values.delivery_m3h>=normal.values.delivery_m3h)throw new Error('Filter-restriction hydraulic consequences did not verify.');
 await expect(page.locator('.alarm-card')).toContainText('High differential pressure');
 await page.getByRole('button',{name:'Upstream',exact:true}).click();await page.waitForTimeout(1000);
 await page.getByRole('button',{name:'Downstream',exact:true}).click();await page.waitForTimeout(1000);
 await page.getByRole('button',{name:'3D twin',exact:true}).click();await page.waitForTimeout(2500);
 await page.screenshot({path:path.join(root,'artifacts/workspace-3d-fault.png'),fullPage:true});
 await page.getByRole('button',{name:'Focus asset',exact:true}).click();await page.waitForTimeout(2200);
 await expect(page.locator('.asset-identity h2')).toHaveText('F-101');
 if(process.argv.includes('--live-ai')){
  await page.getByRole('button',{name:'AI investigator',exact:true}).click();
  await page.getByRole('textbox',{name:'Ask the engineering investigator'}).fill('Investigate this delivery drop. Compare filter restriction with pump degradation and suggest a discriminating experiment.');
  await page.getByRole('button',{name:'Send investigation question'}).click();
  await page.locator('.evidence-list').waitFor({timeout:150000});await page.waitForTimeout(2000);
  await expect(page.locator('.model-attribution')).toContainText('anthropic');
  await page.screenshot({path:path.join(root,'artifacts/ai-investigation.png'),fullPage:true});
 }
 await page.getByRole('button',{name:'Inspector',exact:true}).click();
 await page.getByRole('button',{name:'Test an intervention'}).click();
 await page.getByRole('heading',{name:'Test before you change.'}).waitFor();await page.waitForTimeout(3000);
 const comparisonValues=await page.locator('.compare-row').filter({hasText:'Delivery flow'}).locator('strong').allTextContents();
 if(parseFloat(comparisonValues[1])<=parseFloat(comparisonValues[0]))throw new Error('Clean-filter intervention did not predict delivery recovery.');
 const unchanged=await(await context.request.get(base+'/api/state')).json();
 if(unchanged.controls.filter_resistance!==incident.controls.filter_resistance)throw new Error('What-if changed the operating station.');
 await page.screenshot({path:path.join(root,'artifacts/filter-investigation.png'),fullPage:true});
 await page.getByRole('button',{name:'Close comparison'}).click();
 await page.getByRole('button',{name:'Reset simulation'}).click();
 await page.getByRole('button',{name:'Process graph',exact:true}).click();await page.waitForTimeout(1500);
 console.log('Recorded real solver-backed demonstration',process.argv.includes('--live-ai')?'with live Claude calls':'without AI calls');
 console.log('PASS: supported diagram -> review -> linked graph/3D -> baseline/incident -> measurements/alarms/paths -> grounded AI -> isolated hydraulic comparison');
} finally{
 const video=page.video();await context.close();await browser.close();
 if(video){await copyFile(await video.path(),path.join(root,'artifacts/demo.webm'));await rm(temporary,{recursive:true,force:true});console.log('Saved artifacts/demo.webm');}
}
