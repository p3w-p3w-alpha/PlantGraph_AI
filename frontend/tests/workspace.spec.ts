import {test,expect} from '@playwright/test';
import path from 'node:path';

test.beforeEach(async({page,request})=>{
 await request.post('/api/simulation/action',{data:{action:'reset'}});
 await page.goto('/');
 await expect(page.getByText('Understand the plant.')).toBeVisible();
});

test('links graph, tree, measurements and instrumentation',async({page})=>{
 await expect(page.locator('.react-flow__node')).toHaveCount(13);
 await page.locator('.tree-asset').filter({hasText:'T-101'}).click();
 await expect(page.locator('.asset-identity h2')).toHaveText('T-101');
 await expect(page.locator('.measurement-list')).toContainText('4.00');
 await page.getByTitle('Toggle instrument layer').click();
 await expect(page.locator('.react-flow__node')).toHaveCount(9);
 await page.getByRole('button',{name:'Downstream',exact:true}).click();
 await expect(page.locator('.path-active').first()).toBeVisible();
});

test('filter fault changes solver readings and what-if leaves live controls intact',async({page,request})=>{
 await page.locator('.scenario-button').click();
 await page.locator('.scenario-menu button').filter({hasText:'Filter restriction'}).click();
 await expect(page.locator('.stat-value').first()).toContainText('52.5');
 await expect(page.locator('.alarm-card')).toContainText('High differential pressure');
 await page.getByRole('button',{name:'Test an intervention'}).click();
 await expect(page.getByRole('heading',{name:'Test before you change.'})).toBeVisible();
 await expect(page.locator('.compare-table')).toContainText('69.39');
 const state=await (await request.get('/api/state')).json();
 expect(state.controls.filter_resistance).toBe(80);
 await page.screenshot({path:'../artifacts/filter-investigation.png',fullPage:true});
});

test('healthy standby pump restores pump degradation (backend regression outside v1 demo)',async({page,request})=>{
 await request.post('/api/scenario',{data:{scenario:'pump_degradation',severity:.7}});
 await expect(page.locator('.stat-value').first()).toContainText('40.9');
 await page.locator('.tree-asset').filter({hasText:'P-101A'}).click();
 await page.getByRole('button',{name:'Pump B',exact:true}).click();
 await expect(page.locator('.stat-value').first()).toContainText('69.4');
 await expect(page.locator('.status-badge')).toHaveText(/STANDBY/);
});

test('clock runs, pauses, and reset restores baseline',async({page,request})=>{
 await page.getByRole('button',{name:'Play simulation',exact:true}).click();
 await expect.poll(async()=> (await (await request.get('/api/state')).json()).elapsed_s).toBeGreaterThan(10);
 await page.getByRole('button',{name:'Pause simulation',exact:true}).click();
 const paused=await (await request.get('/api/state')).json();
 await page.waitForTimeout(1200);
 const later=await (await request.get('/api/state')).json();
 expect(later.elapsed_s).toBe(paused.elapsed_s);
 await page.getByRole('button',{name:'Reset simulation'}).click();
 await expect(page.locator('.transport-clock')).toHaveText('00:00:00');
});

test('3D investigation shares selection and exposes live filter evidence',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.getByRole('button',{name:'3D twin',exact:true}).click();
 await expect(page.locator('canvas')).toBeVisible();
 await page.getByRole('button',{name:'Focus asset',exact:true}).click();
 await page.waitForTimeout(1200);
 await page.getByRole('button',{name:'Overview',exact:true}).click();
 await page.waitForTimeout(1600);
 await page.getByRole('button',{name:/T-101.*m/}).click();
 await expect(page.locator('.asset-identity h2')).toHaveText('T-101');
 await page.getByRole('button',{name:'Top',exact:true}).click();
 await page.waitForTimeout(1000);
 await page.screenshot({path:'../artifacts/3d-investigation.png',fullPage:true});
 expect(errors).toEqual([]);
});

test('exports an investigation record with provenance and no secret',async({page})=>{
 const downloadPromise=page.waitForEvent('download');
 await page.getByRole('button',{name:'Export investigation'}).click();
 const download=await downloadPromise;
 expect(download.suggestedFilename()).toBe('plantgraph-investigation.json');
 const stream=await download.createReadStream();let content='';for await(const chunk of stream!)content+=chunk;
 const record=JSON.parse(content);
 expect(record.plant.id).toBe('atlas-station-01');
 expect(record.state.provenance).toContain('Physics-generated');
 expect(content).not.toContain('sk-ant-');
});

test('unmapped imported drawing clears prior context and cannot inherit station data',async({page})=>{
 await page.route('**/api/ai/chat',r=>r.fulfill({json:{answer:'Previous station diagnosis',evidence:[],hypotheses:[],suggested_actions:[],source:'recorded',model:'test-fixture'}}));
 await page.getByRole('button',{name:'AI investigator',exact:true}).click();
 await page.getByRole('textbox',{name:'Ask the engineering investigator'}).fill('Summarize this station');
 await page.getByRole('button',{name:'Send investigation question'}).click();
 await expect(page.getByText('Previous station diagnosis')).toBeVisible();
 await page.route('**/api/ai/extract',r=>r.fulfill({json:{document_id:'fixture-drawing',assets:[{id:'HX-901',type:'heat_exchanger',name:'External exchanger',bbox:[.1,.2,.4,.6],confidence:.8}],connections:[],uncertainties:['Hydraulic parameters missing'],summary:'Independent drawing test fixture',source:'recorded',model:'test-fixture',validation:{valid:false,missing_assets:['F-101'],extra_assets:['HX-901'],missing_connections:[]}}}));
 await page.route('**/api/ai/review',r=>r.fulfill({json:{accepted:true,simulation_ready:false,issues:['Unmapped heat exchanger']}}));
 await page.getByRole('button',{name:'Try the station P&ID'}).click();
 await expect(page.getByRole('heading',{name:'Review the extracted plant.'})).toBeVisible();
 await page.getByRole('button',{name:'Confirm reviewed model'}).click();
 await expect(page.getByText('Previous station diagnosis')).toHaveCount(0);
 await expect(page.locator('.metrics-row')).not.toContainText('69.4');
 await expect(page.getByRole('button',{name:'Play simulation'})).toBeDisabled();
 await page.getByRole('button',{name:'3D twin',exact:true}).click();
 await expect(page.getByRole('heading',{name:'3D model not mapped'})).toBeVisible();
 await page.getByRole('button',{name:'Inspector',exact:true}).click();
 await expect(page.locator('.asset-identity h2')).toHaveText('HX-901');
});

test('live Claude extracts the actual station image and engineer binds it',async({page})=>{
 test.skip(process.env.LIVE_AI!=='1','Set LIVE_AI=1 to make paid Anthropic calls.');
 await page.getByRole('button',{name:'Try the station P&ID'}).click();
 await expect(page.getByRole('heading',{name:'Review the extracted plant.'})).toBeVisible({timeout:110000});
 const assets=JSON.parse(await page.getByRole('textbox',{name:'Review extracted equipment'}).inputValue());
 expect(assets.map((a:any)=>a.id)).toEqual(expect.arrayContaining(['T-101','P-101A','P-101B','F-101','V-101','V-102']));
 await page.getByRole('button',{name:'Confirm reviewed model'}).click();
 await expect(page.getByText('Reviewed drawing · hydraulic mapping verified')).toBeVisible();
 await expect(page.getByRole('button',{name:'Play simulation'})).toBeEnabled();
});

test('live copilot supplies evidence and a typed diagnostic action',async({page})=>{
 test.skip(process.env.LIVE_AI!=='1','Set LIVE_AI=1 to make paid Anthropic calls.');
 await page.locator('.scenario-button').click();
 await page.locator('.scenario-menu button').filter({hasText:'Filter restriction'}).click();
 await page.getByRole('button',{name:'AI investigator',exact:true}).click();
 await page.getByRole('textbox',{name:'Ask the engineering investigator'}).fill('Investigate the falling delivery flow. Explain the evidence and a useful diagnostic experiment.');
 await page.getByRole('button',{name:'Send investigation question'}).click();
 await expect(page.locator('.evidence-list')).toBeVisible({timeout:110000});
 await expect(page.locator('.assistant-text')).toContainText(/filter|pressure/i);
 await expect(page.locator('.model-attribution')).toContainText('anthropic');
 await page.screenshot({path:'../artifacts/ai-investigation.png',fullPage:true});
});

test('live natural-language valve experiment reaches a real isolated hydraulic comparison',async({page,request})=>{
 test.skip(process.env.LIVE_AI!=='1','Set LIVE_AI=1 to make paid Anthropic calls.');
 await page.getByRole('button',{name:'AI investigator',exact:true}).click();
 await page.getByRole('textbox',{name:'Ask the engineering investigator'}).fill('What happens if V-101 is set to 30 percent opening? Give me a what_if action with valve_open_pct 30, then let the hydraulic solver calculate the result.');
 await page.getByRole('button',{name:'Send investigation question'}).click();
 await expect(page.locator('.suggested-action').filter({hasText:/30/}).first()).toBeVisible({timeout:110000});
 await page.locator('.suggested-action').filter({hasText:/30/}).first().click();
 await expect(page.getByRole('heading',{name:'Test before you change.'})).toBeVisible();
 const row=page.locator('.compare-row').filter({hasText:'Delivery flow'});
 const values=await row.locator('strong').allTextContents();
 expect(parseFloat(values[1])).toBeLessThan(parseFloat(values[0]));
 const state=await (await request.get('/api/state')).json();expect(state.controls.valve_open_pct).toBe(100);
});
