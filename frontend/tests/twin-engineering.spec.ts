import {test,expect,type Page} from '@playwright/test';

async function readCanvas(page:Page,key:string){return page.locator('.twin-canvas-wrap canvas').evaluate((c,k)=>JSON.parse((c as HTMLCanvasElement).dataset[k]||'null'),key);}
async function clickMesh(page:Page,id:string,double=false){
 const canvas=page.locator('.twin-canvas-wrap canvas');
 await expect.poll(async()=>!!(await readCanvas(page,'assetScreenPositions'))?.[id]?.visible).toBe(true);
 const point=(await readCanvas(page,'assetScreenPositions'))[id],rect=(await canvas.boundingBox())!;
 const x=rect.x+point.x,y=rect.y+point.y;
 expect(await page.evaluate(({x,y})=>document.elementFromPoint(x,y)?.tagName,{x,y})).toBe('CANVAS');
 if(double)await page.mouse.dblclick(x,y);else await page.mouse.click(x,y);
}
test.beforeEach(async({page,request})=>{
 await request.post('/api/simulation/action',{data:{action:'reset'}});
 await page.goto('/');await page.getByText('Understand the plant.').waitFor();
 await page.getByRole('button',{name:'3D twin',exact:true}).click();
 await expect(page.locator('.twin-canvas-wrap canvas')).toBeVisible();
 await expect.poll(async()=>!!await readCanvas(page,'cameraState')).toBe(true);
 await page.waitForTimeout(1300);
});

test('actual equipment mesh clicks synchronize inspector and graph; double-click focuses',async({page})=>{
 await clickMesh(page,'T-101');await expect(page.locator('.asset-identity h2')).toHaveText('T-101');
 await clickMesh(page,'F-101');await expect(page.locator('.asset-identity h2')).toHaveText('F-101');
 const before=await readCanvas(page,'cameraState');
 await clickMesh(page,'F-101',true);await page.waitForTimeout(1600);
 const after=await readCanvas(page,'cameraState');
 expect(after.distance).toBeLessThan(before.distance-1);
 await page.getByRole('button',{name:'Process graph',exact:true}).click();
 await expect(page.locator('.react-flow__node[data-id="F-101"] .is-selected')).toBeVisible();
});

test('drag orbits and scroll zooms the actual 3D camera',async({page})=>{
 const canvas=page.locator('.twin-canvas-wrap canvas'),rect=(await canvas.boundingBox())!;
 const before=await readCanvas(page,'cameraState');
 const x=rect.x+rect.width*.7,y=rect.y+rect.height*.65;
 await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+100,y-35,{steps:15});await page.mouse.up();await page.waitForTimeout(700);
 const orbited=await readCanvas(page,'cameraState');expect(orbited.quaternion).not.toEqual(before.quaternion);
 await page.mouse.move(rect.x+rect.width*.5,rect.y+rect.height*.5);await page.mouse.wheel(0,-220);await page.waitForTimeout(700);
 const zoomed=await readCanvas(page,'cameraState');expect(zoomed.distance).toBeLessThan(orbited.distance);
});

test('visible above-pipe flow arrows move only during playback; standby and zero flow have none',async({page,request})=>{
 const arrows=await readCanvas(page,'flowArrows');expect(arrows.length).toBeGreaterThan(2);
 expect(arrows.some((r:any)=>r.points.some((p:number[])=>p[2]<-1))).toBe(true);
 expect(arrows.some((r:any)=>r.points.some((p:number[])=>p[2]>1))).toBe(false);
 for(const route of arrows){expect(route.flow).toBeGreaterThan(0);expect(route.positions.length).toBeGreaterThan(0);}
 const frozen=JSON.stringify(arrows.map((a:any)=>a.positions));await page.waitForTimeout(400);
 expect(JSON.stringify((await readCanvas(page,'flowArrows')).map((a:any)=>a.positions))).toBe(frozen);
 await page.getByRole('button',{name:'Play simulation',exact:true}).click();
 await expect.poll(async()=>(await readCanvas(page,'flowState'))?.playing).toBe(true);
 const moving=JSON.stringify((await readCanvas(page,'flowArrows')).map((a:any)=>a.positions));await page.waitForTimeout(400);
 expect(JSON.stringify((await readCanvas(page,'flowArrows')).map((a:any)=>a.positions))).not.toBe(moving);
 await page.getByRole('button',{name:'Pause simulation',exact:true}).click();
 await expect.poll(async()=>(await readCanvas(page,'flowState'))?.playing).toBe(false);
 const stopped=JSON.stringify((await readCanvas(page,'flowArrows')).map((a:any)=>a.positions));await page.waitForTimeout(400);
 expect(JSON.stringify((await readCanvas(page,'flowArrows')).map((a:any)=>a.positions))).toBe(stopped);
 await request.post('/api/control',{data:{outlet_open:false}});
 await expect.poll(async()=>(await readCanvas(page,'flowArrows'))?.length).toBe(0);
 await expect.poll(async()=>(await readCanvas(page,'flowState'))?.delivery_m3h).toBe(0);
});

test('3D filter alarm, path tracing and clean-filter comparison remain in the operating workspace',async({page,request})=>{
 await request.post('/api/scenario',{data:{scenario:'filter_clogging',severity:.7}});
 const label=page.getByTestId('twin-label-F-101');await expect(label).toContainText('HIGH ΔP');
 await expect(label).toContainText('PT-101 inlet');await expect(label).toContainText('PT-102 outlet');await expect(label).toContainText('1.38 bar');
 const workspace=page.locator('.twin-canvas-wrap');
 await workspace.getByRole('button',{name:/Upstream/}).click();await expect(page.locator('.path-buttons button').filter({hasText:'Upstream'})).toHaveClass(/active/);
 await workspace.getByRole('button',{name:/Downstream/}).click();await expect(page.locator('.path-buttons button').filter({hasText:'Downstream'})).toHaveClass(/active/);
 const before=await(await request.get('/api/state')).json();
 await workspace.getByRole('button',{name:/Test intervention/}).click();
 await expect(page.getByRole('heading',{name:'Test before you change.'})).toBeVisible();
 await expect(page.locator('.comparison-modal')).toContainText('WHAT-IF RESULT');
 const values=await page.locator('.compare-row').filter({hasText:'Delivery flow'}).locator('strong').allTextContents();
 expect(parseFloat(values[1])).toBeGreaterThan(parseFloat(values[0]));
 const after=await(await request.get('/api/state')).json();expect(after.controls).toEqual(before.controls);expect(after.elapsed_s).toBe(before.elapsed_s);
 await page.getByRole('button',{name:'Close comparison'}).click();await expect(page.locator('.twin-canvas-wrap canvas')).toBeVisible();
 await page.screenshot({path:'../artifacts/3d-engineering-investigation.png',fullPage:true});
});
