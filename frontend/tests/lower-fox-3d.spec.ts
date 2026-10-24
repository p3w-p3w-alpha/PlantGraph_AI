import {test,expect,type Locator,type Page} from '@playwright/test';

type ScreenPoint={x:number;y:number;visible:boolean};
async function canvasOf(page:Page){const canvas=page.locator('.generic-twin canvas');await expect(canvas).toBeVisible();await expect(canvas).toHaveAttribute('data-asset-screen-positions',/^\{/);return canvas}
async function data(canvas:Locator,key:string){return JSON.parse((await canvas.getAttribute('data-'+key))||'null')}
async function meshClick(page:Page,canvas:Locator,id:string,double=false){const points=await data(canvas,'asset-screen-positions') as Record<string,ScreenPoint>;expect(points[id]?.visible,`${id} must be projected inside viewport`).toBeTruthy();const box=await canvas.boundingBox();expect(box).not.toBeNull();if(double)await page.mouse.dblclick(box!.x+points[id].x,box!.y+points[id].y);else await page.mouse.click(box!.x+points[id].x,box!.y+points[id].y)}
async function overview(page:Page){await page.locator('.generic-twin').getByRole('button',{name:'Overview',exact:true}).click();await page.waitForTimeout(1100)}
async function settledCamera(canvas:Locator){let previous:any=null,stable=0;await expect.poll(async()=>{const current=await data(canvas,'camera-state');if(previous&&current.position.every((n:number,i:number)=>Math.abs(n-previous.position[i])<.02))stable++;else stable=0;previous=current;return stable},{timeout:10000,intervals:[180]}).toBeGreaterThanOrEqual(3);return previous}
function shape(arrows:any[]){return arrows.map(route=>({route:route.route,positions:route.positions}))}

let originalCase='atlas-station-01';
test.describe('Lower Fox canonical case — real 3D engineering interactions',()=>{
 test.beforeAll(async({request})=>{const plant=await request.get('/api/plant');if(plant.ok())originalCase=(await plant.json()).id});
 test.beforeEach(async({request,page})=>{const selected=await request.post('/api/cases/select',{data:{case_id:'lower-fox-river'}});expect(selected.ok()).toBeTruthy();await page.goto('/');await canvasOf(page);await page.waitForTimeout(1600)});
 test.afterAll(async({request})=>{await request.post('/api/simulation/action',{data:{action:'pause'}});await request.post('/api/cases/select',{data:{case_id:originalCase}})});

 test('canonical equipment geometry, actual mesh selection, labels, focus and camera navigation',async({page,request})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));const canvas=await canvasOf(page);const plant=await(await request.get('/api/plant')).json();
  const rendered=await data(canvas,'scene-assets');expect(rendered.map((a:any)=>a.id).sort()).toEqual(plant.assets.map((a:any)=>a.id).sort());
  expect(rendered.filter((a:any)=>a.type==='filter')).toHaveLength(3);expect(rendered.filter((a:any)=>a.type==='pump')).toHaveLength(3);expect(rendered.filter((a:any)=>a.type==='tank')).toHaveLength(1);expect(rendered.some((a:any)=>/^(?:T-101|F-101|P-101)/.test(a.id))).toBeFalsy();
  // Each click lands on the projected equipment body inside the WebGL canvas,
  // rather than on the DOM tag or hierarchy tree.
  for(const id of ['CF1','CF2','CF3','P-2A','P-2B','P-2C','ET']){await meshClick(page,canvas,id);await expect(page.locator('.asset-identity h2')).toHaveText(id);await expect.poll(async()=>{const assets=await data(canvas,'scene-assets');return assets.find((a:any)=>a.id===id)?.selected}).toBe(true)}
  await meshClick(page,canvas,'CF2');const beforeFocus=await data(canvas,'camera-state');await page.getByTestId('twin-label-CF2').dblclick();await expect.poll(async()=>(await data(canvas,'camera-state')).distance).toBeLessThan(beforeFocus.distance*.7);await expect(page.locator('.asset-identity h2')).toHaveText('CF2');
  await overview(page);await meshClick(page,canvas,'P-2A',true);await expect.poll(async()=>(await data(canvas,'camera-state')).distance).toBeLessThan(8);await overview(page);
  const box=(await canvas.boundingBox())!,beforeOrbit=await data(canvas,'camera-state');await page.mouse.move(box.x+box.width*.12,box.y+box.height*.52);await page.mouse.down();await page.mouse.move(box.x+box.width*.12+65,box.y+box.height*.52+18,{steps:8});await page.mouse.up();const orbited=await settledCamera(canvas);expect(orbited.quaternion).not.toEqual(beforeOrbit.quaternion);
  await meshClick(page,canvas,'ET');await expect(page.locator('.asset-identity h2')).toHaveText('ET');await page.waitForTimeout(450);const afterSelection=await data(canvas,'camera-state');expect(afterSelection.position.every((n:number,i:number)=>Math.abs(n-orbited.position[i])<.2)).toBeTruthy();
  const wheel={x:box.x+box.width*.06,y:box.y+box.height*.65};expect(await page.evaluate(({x,y})=>document.elementFromPoint(x,y)?.tagName,wheel)).toBe('CANVAS');await page.mouse.move(wheel.x,wheel.y);await page.mouse.wheel(0,-230);await expect.poll(async()=>(await data(canvas,'camera-state')).distance).toBeLessThan(orbited.distance*.99);await overview(page);await page.screenshot({path:'../artifacts/lower-fox-3d-mesh-selection.png'});expect(errors).toEqual([]);
 });

 test('visible arrow geometry follows play/pause and excludes isolated filters and spare pumps',async({page,request})=>{
  const canvas=await canvasOf(page),state=await(await request.get('/api/state')).json();let arrows=await data(canvas,'flow-arrows');expect(arrows.length).toBeGreaterThan(10);expect(arrows.every((route:any)=>route.visible&&route.flow>0&&route.positions.length>0)).toBeTruthy();
  const offlineIds=Object.entries(state.equipment).filter(([,v]:any)=>['offline','standby','spare','closed','tripped'].includes(v.status)).map(([id])=>id);expect(arrows.some((route:any)=>offlineIds.includes(route.from)||offlineIds.includes(route.to))).toBeFalsy();
  const paused=shape(arrows);await page.waitForTimeout(450);expect(shape(await data(canvas,'flow-arrows'))).toEqual(paused);
  await page.getByRole('button',{name:'Play simulation',exact:true}).click();await expect.poll(async()=>(await data(canvas,'flow-state')).playing).toBe(true);const moving=shape(await data(canvas,'flow-arrows'));await page.waitForTimeout(500);expect(shape(await data(canvas,'flow-arrows'))).not.toEqual(moving);
  await page.getByRole('button',{name:'Pause simulation',exact:true}).click();await expect.poll(async()=>(await data(canvas,'flow-state')).playing).toBe(false);await page.waitForTimeout(150);const stopped=shape(await data(canvas,'flow-arrows'));await page.waitForTimeout(400);expect(shape(await data(canvas,'flow-arrows'))).toEqual(stopped);
  const tank=(await data(canvas,'scene-assets')).find((asset:any)=>asset.type==='tank');const current=await(await request.get('/api/state')).json();expect(tank.water_height).toBeCloseTo(current.asset_values[tank.id].level_pct/100*3.15,3);await page.screenshot({path:'../artifacts/lower-fox-visible-flow.png'});
 });

 test('direct 3D tracing and graph selection stay synchronized',async({page})=>{
  const canvas=await canvasOf(page);await meshClick(page,canvas,'CF1');await page.locator('.generic-twin').getByRole('button',{name:/Downstream/}).click();await expect.poll(async()=>(await data(canvas,'scene-assets')).find((asset:any)=>asset.id==='DIFFUSER')?.highlighted).toBe(true);
  const highlighted=(await data(canvas,'scene-assets')).filter((asset:any)=>asset.highlighted).map((asset:any)=>asset.id);expect(highlighted).toEqual(expect.arrayContaining(['CF1','FILTRATE-HEADER','ET','P-2A','P-2B','P-2C','DIFFUSER']));expect(highlighted).not.toContain('CF2');expect(highlighted).not.toContain('CF3');
  await meshClick(page,canvas,'ET');await page.getByRole('button',{name:'Process graph',exact:true}).click();await expect(page.locator('.react-flow__node[data-id="ET"]')).toHaveClass(/selected/);await page.getByRole('button',{name:'3D twin',exact:true}).click();await canvasOf(page);await expect(page.locator('.asset-identity h2')).toHaveText('ET');await page.screenshot({path:'../artifacts/lower-fox-3d-trace.png'});
 });

 test('computed inventory warning, pressure evidence and zero-flow shutdown reflect solver state',async({page,request})=>{
  const canvas=await canvasOf(page),normal=await(await request.get('/api/state')).json();const response=await request.post('/api/scenario',{data:{scenario:'filter_fouling',asset_id:'CF1',severity:1}});expect(response.ok()).toBeTruthy();const fouled=await response.json();expect(fouled.metrics.inflow_m3h).toBeLessThan(normal.metrics.inflow_m3h);expect(fouled.metrics.outflow_m3h).toBeCloseTo(normal.metrics.outflow_m3h,1);expect(fouled.metrics.mass_balance_m3h).toBeLessThan(0);expect(fouled.alarms.find((alarm:any)=>alarm.id==='MODEL-INVENTORY-IMBALANCE')?.provenance).toBe('computed_model_only');
  await expect.poll(async()=>(await data(canvas,'scene-assets')).find((asset:any)=>asset.id==='ET')?.alarmed).toBe(true);await meshClick(page,canvas,'ET');await expect(page.locator('.alarm-card')).toContainText('model-only diagnostic');
  await meshClick(page,canvas,'CF1');await expect(page.getByTestId('twin-label-CF1')).toContainText(fouled.asset_values.CF1.dp_bar.toFixed(2));await page.screenshot({path:'../artifacts/lower-fox-filter-inventory-warning.png'});
  const shutdown=await request.post('/api/scenario',{data:{scenario:'pump_degradation',asset_id:'P-2A',severity:1}});expect(shutdown.ok()).toBeTruthy();const stopped=await shutdown.json();expect(stopped.metrics.outflow_m3h).toBe(0);await expect.poll(async()=>(await data(canvas,'flow-state')).outflow_m3h).toBe(0);const rendered=await data(canvas,'flow-arrows');expect(rendered.some((route:any)=>['P-2A','P-2B','P-2C'].includes(route.from)||['P-2A','P-2B','P-2C'].includes(route.to))).toBeFalsy();expect(rendered.some((route:any)=>route.to==='DIFFUSER')).toBeFalsy();await page.screenshot({path:'../artifacts/lower-fox-pump-shutdown.png'});
 });
});
