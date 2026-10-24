import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame, useThree, type ThreeEvent } from '@react-three/fiber'
import { OrbitControls, ContactShadows, Line } from '@react-three/drei'
import * as THREE from 'three'
import type { Plant, State } from '../types'

type Props = { plant: Plant; state: State | null; selectedId: string | null; onSelect: (id: string) => void; highlightedIds?: string[]; showLabels?: boolean; onTrace?: (direction:'upstream'|'downstream')=>void; onAskAI?: (id:string)=>void; onTestIntervention?: (id:string)=>void }
type V3 = [number, number, number]
const positions: Record<string, V3> = { 'T-101': [-5, 1.7, 0], 'P-101A': [-2.4, .8, -1.55], 'P-101B': [-2.4, .8, 1.55], 'F-101': [1.2, 1.5, 0], 'V-101': [3.3, 1.05, 0], 'V-102': [4.9, 1.05, 0], OUTLET: [6.35, 1.05, 0], 'J-SUCTION': [-3.6,.8,0], 'J-DISCHARGE': [-.7,1.05,0] }
const colors = { pipe: '#486276', tank: '#72899b', teal: '#62e7d1', blue: '#62caff', warning: '#ffbd66', alarm: '#ff756f', dark: '#162535' }
const labelBase: React.CSSProperties = { width: 74, border: '1px solid #354858', borderRadius: 5, padding: '4px 6px', background: 'rgba(10,19,29,.86)', color:'#e5eef6', fontFamily:'Inter, sans-serif', fontSize:9, boxShadow:'0 3px 12px #0004', cursor:'pointer', userSelect:'none' }
const labelPositions:Record<string,V3>={'T-101':[-5,4.2,.1],'P-101A':[-2.4,1.65,-1.55],'P-101B':[-2.4,1.65,1.55],'F-101':[1.2,3.7,0],'V-101':[3.3,2.05,0],'V-102':[5.1,2.05,0]}
function CylinderBetween({ a, b, radius=.095, color=colors.pipe, emissive, opacity=1 }: {a:V3;b:V3;radius?:number;color?:string;emissive?:string;opacity?:number}) {
 const {mid,quaternion,length}=useMemo(()=>{const av=new THREE.Vector3(...a),bv=new THREE.Vector3(...b); const direction=bv.clone().sub(av);return {mid:av.add(bv).multiplyScalar(.5),quaternion:new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),direction.clone().normalize()),length:direction.length()}},[a.join(','),b.join(',')])
 return <mesh position={mid} quaternion={quaternion} castShadow receiveShadow><cylinderGeometry args={[radius,radius,length,16]}/><meshStandardMaterial color={color} metalness={.65} roughness={.35} emissive={emissive||'#000'} emissiveIntensity={.25} transparent={opacity<1} opacity={opacity}/></mesh>
}
function BoltRing({position, radius, rotation=[0,0,0]}:{position:V3;radius:number;rotation?:V3}){return <group position={position} rotation={rotation}><mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[radius,.035,8,40]}/><meshStandardMaterial color="#acc1cc" metalness={.82} roughness={.24}/></mesh>{Array.from({length:8},(_,i)=><mesh key={i} position={[Math.cos(i*Math.PI/4)*radius,0,Math.sin(i*Math.PI/4)*radius]}><cylinderGeometry args={[.035,.035,.04,6]}/><meshStandardMaterial color="#cad8de" metalness={.8}/></mesh>)}</group>}
function Flow({points,flow,enabled=true,playing=false}:{points:V3[];flow:number;enabled?:boolean;playing?:boolean}) {
 const refs=useRef<(THREE.Group|null)[]>([]),phase=useRef(0)
 const path=useMemo(()=>{const curve=new THREE.CurvePath<THREE.Vector3>();for(let i=0;i<points.length-1;i++){const a=new THREE.Vector3(...points[i]),b=new THREE.Vector3(...points[i+1]);a.y+=.2;b.y+=.2;curve.add(new THREE.LineCurve3(a,b))}return curve},[JSON.stringify(points)])
 const count=Math.max(1,Math.min(7,Math.ceil(path.getLength()/1.15)))
 const up=useMemo(()=>new THREE.Vector3(0,1,0),[]),direction=useMemo(()=>new THREE.Vector3(),[])
 useFrame((_,delta)=>{if(!enabled||Math.abs(flow)<.01)return;if(playing)phase.current=(phase.current+Math.sign(flow)*delta*Math.min(Math.abs(flow)/180,.65)+1)%1;refs.current.forEach((arrow,i)=>{if(!arrow)return;const t=(phase.current+(i+.5)/count)%1;arrow.position.copy(path.getPoint(t));direction.copy(path.getTangent(t)).multiplyScalar(Math.sign(flow));arrow.quaternion.setFromUnitVectors(up,direction)})})
 if(!enabled||Math.abs(flow)<.01)return null
 return <group name="hydraulic-flow-direction" userData={{flow,playing,points}}>{Array.from({length:count},(_,i)=><group key={i} ref={m=>{refs.current[i]=m}}><mesh renderOrder={3}><coneGeometry args={[.085,.24,10]}/><meshBasicMaterial color="#69f5ee" toneMapped={false}/></mesh><mesh position={[0,-.16,0]} renderOrder={3}><cylinderGeometry args={[.025,.025,.16,8]}/><meshBasicMaterial color="#69f5ee" toneMapped={false}/></mesh></group>)}</group>
}
function Pipe({points,flow,lit,enabled=true,playing=false,onClick}:{points:V3[];flow:number;lit?:boolean;enabled?:boolean;playing?:boolean;onClick?:()=>void}){return <group onClick={e=>{if(onClick){e.stopPropagation();onClick()}}}>{points.slice(0,-1).map((point,i)=><CylinderBetween key={i} a={point} b={points[i+1]} radius={lit?.115:.095} color={lit?'#519c9c':colors.pipe} emissive={lit?colors.teal:undefined}/>)}{points.slice(1,-1).map((point,i)=><mesh key={i} position={point}><sphereGeometry args={[.105,12,10]}/><meshStandardMaterial color={lit?'#519c9c':colors.pipe} metalness={.7} roughness={.35}/></mesh>)}<Flow points={points} flow={flow} enabled={enabled} playing={playing}/></group>}

function LabelProjector({elements,selectedId,state}:{elements:React.RefObject<Record<string,HTMLButtonElement|null>>;selectedId:string|null;state:State|null}) {
 const {camera,size,gl,scene}=useThree(),orbit=useThree(s=>s.controls) as any
 const projected=useMemo(()=>new THREE.Vector3(),[]),lastMetadata=useRef(0)
 useFrame(({clock})=>{const occupied:{x:number;y:number;width:number;height:number}[]=[];const ids=Object.keys(labelPositions).sort((a,b)=>(a===selectedId?-1:b===selectedId?1:0));for(const id of ids){const element=elements.current[id];if(!element)continue;projected.set(...labelPositions[id]).project(camera);const x=(projected.x*.5+.5)*size.width,y=(-projected.y*.5+.5)*size.height,width=element.offsetWidth,height=element.offsetHeight;const blocked=occupied.some(other=>Math.abs(other.x-x)<(other.width+width)/2+3&&Math.abs(other.y-y)<(other.height+height)/2+3);const visible=projected.z>-1&&projected.z<1&&x>25&&x<size.width-25&&y>35&&y<size.height-75&&!blocked;element.style.opacity=visible?'1':'0';element.style.pointerEvents=visible?'auto':'none';element.style.transform=`translate3d(${x}px,${y}px,0) translate(-50%,-50%)`;if(visible)occupied.push({x,y,width,height})}
 // Read-only screen projections support repeatable canvas interaction checks.
 if(clock.elapsedTime-lastMetadata.current>.1){lastMetadata.current=clock.elapsedTime;const screen:Record<string,{x:number;y:number;visible:boolean}>={};for(const id of ['T-101','P-101A','P-101B','F-101','V-101','V-102']){projected.set(...positions[id]).project(camera);screen[id]={x:(projected.x*.5+.5)*size.width,y:(-projected.y*.5+.5)*size.height,visible:projected.z>-1&&projected.z<1&&Math.abs(projected.x)<1&&Math.abs(projected.y)<1}}gl.domElement.dataset.assetScreenPositions=JSON.stringify(screen);gl.domElement.dataset.cameraState=JSON.stringify({position:camera.position.toArray(),quaternion:camera.quaternion.toArray(),target:orbit?.target?.toArray(),distance:orbit?.getDistance?.()});gl.domElement.dataset.flowState=JSON.stringify({playing:!!state?.playing,delivery_m3h:state?.values.delivery_m3h??0,pump_outflow_m3h:(state?.values.delivery_m3h??0)+(state?.values.leak_m3h??0),active_pump:state?.controls.active_pump??null});const arrows:unknown[]=[];scene.traverse(object=>{if(object.name==='hydraulic-flow-direction')arrows.push({route:object.userData.points.map((p:number[])=>p.join(',')).join('|'),flow:object.userData.flow,playing:object.userData.playing,visible:object.visible,start:object.userData.points[0],end:object.userData.points.at(-1),points:object.userData.points,positions:object.children.map(arrow=>arrow.position.toArray()),arrows:object.children.map(arrow=>({position:arrow.position.toArray(),quaternion:arrow.quaternion.toArray()}))})});gl.domElement.dataset.flowArrows=JSON.stringify(arrows)}
 })
 return null
}

function Equipment({id,selected,highlighted,alarmed,onSelect,onFocus,children}:{id:string;selected:boolean;highlighted:boolean;alarmed:boolean;onSelect:(id:string)=>void;onFocus:(id:string)=>void;children:React.ReactNode}){
 const [hover,setHover]=useState(false)
 const p=positions[id]
 const color=alarmed?colors.alarm:selected?colors.blue:colors.teal
 return <group name={`equipment-${id}`} onClick={(e:ThreeEvent<MouseEvent>)=>{e.stopPropagation();onSelect(id)}} onDoubleClick={(e:ThreeEvent<MouseEvent>)=>{e.stopPropagation();onSelect(id);onFocus(id)}} onPointerOver={e=>{e.stopPropagation();setHover(true);document.body.style.cursor='pointer'}} onPointerOut={()=>{setHover(false);document.body.style.cursor='auto'}}>{children}{(selected||hover||highlighted||alarmed)&&<mesh position={[p[0],.13,p[2]]} rotation={[-Math.PI/2,0,0]}><ringGeometry args={[id==='T-101'?1.35:id==='F-101'?.9:.65,id==='T-101'?1.4:id==='F-101'?.95:.7,64]}/><meshBasicMaterial color={color} transparent opacity={selected?1:.65} side={THREE.DoubleSide}/></mesh>}</group>
}
function Tank({level}:{level:number}){const waterHeight=Math.max(.08,Math.min(level/6,1)*3.15);return <group position={[-5,0,0]}>
 <mesh position={[0,.26,0]} castShadow><cylinderGeometry args={[1.25,1.3,.25,48]}/><meshStandardMaterial color="#273d4d" metalness={.6} roughness={.6}/></mesh>
 <mesh position={[0,1.95,0]} castShadow><cylinderGeometry args={[1.13,1.13,3.25,64,1,true]}/><meshPhysicalMaterial color="#9cbdcf" metalness={.25} roughness={.12} transparent opacity={.24} side={THREE.DoubleSide} depthWrite={false}/></mesh>
 <mesh position={[0,.36+waterHeight/2,0]}><cylinderGeometry args={[1.095,1.095,waterHeight,48]}/><meshPhysicalMaterial color="#11779c" emissive="#12556b" emissiveIntensity={.35} transparent opacity={.78} metalness={.15} roughness={.13}/></mesh>
 <mesh position={[0,.37+waterHeight,0]} rotation={[-Math.PI/2,0,0]}><circleGeometry args={[1.1,48]}/><meshStandardMaterial color="#58d4e7" transparent opacity={.65} roughness={.15}/></mesh>
 {[.38,1.15,2.4,3.55].map(y=><BoltRing key={y} position={[0,y,0]} radius={1.15}/>)}
 <mesh position={[0,3.63,0]} castShadow><cylinderGeometry args={[.93,1.13,.18,48]}/><meshStandardMaterial color={colors.tank} metalness={.75} roughness={.3}/></mesh>
 <mesh position={[0,3.76,0]}><cylinderGeometry args={[.35,.35,.12,32]}/><meshStandardMaterial color="#314d60" metalness={.8}/></mesh>
 <CylinderBetween a={[.4,3.7,0]} b={[.4,4.0,0]} radius={.04}/>
 <mesh position={[.4,4.02,0]}><cylinderGeometry args={[.1,.1,.06,16]}/><meshStandardMaterial color="#a8c3cf" metalness={.8}/></mesh>
 <CylinderBetween a={[-.5,.4,-1.1]} b={[-.5,3.55,-1.1]} radius={.025}/><CylinderBetween a={[.05,.4,-1.1]} b={[.05,3.55,-1.1]} radius={.025}/>
 {Array.from({length:10},(_,i)=><CylinderBetween key={i} a={[-.5,.55+i*.3,-1.12]} b={[.05,.55+i*.3,-1.12]} radius={.018}/>)}
 <mesh position={[.73,1.9,.87]}><boxGeometry args={[.03,2.9,.03]}/><meshStandardMaterial color="#d3e1e8"/></mesh>
 {Array.from({length:7},(_,i)=><mesh key={i} position={[.76,.55+i*.45,.87]}><boxGeometry args={[.15,.02,.02]}/><meshStandardMaterial color="#d3e1e8"/></mesh>)}
 </group>}
function Pump({z,running,speed,playing=false}:{z:number;running:boolean;speed:number;playing?:boolean}){const fan=useRef<THREE.Group>(null);useFrame((_,d)=>{if(fan.current&&running&&playing)fan.current.rotation.x+=d*speed*.2});return <group position={[-2.4,0,z]}>
 <mesh position={[0,.18,0]} castShadow><boxGeometry args={[1.75,.22,.85]}/><meshStandardMaterial color="#253d4a" metalness={.6}/></mesh>
 {[-.55,.55].map(x=><mesh key={x} position={[x,.39,0]}><boxGeometry args={[.22,.3,.46]}/><meshStandardMaterial color="#435f6e" metalness={.6}/></mesh>)}
 <mesh position={[.12,.75,0]} rotation={[0,0,Math.PI/2]} castShadow><cylinderGeometry args={[.32,.32,.9,32]}/><meshStandardMaterial color={running?'#286e79':'#415765'} metalness={.7} roughness={.3}/></mesh>
 {Array.from({length:7},(_,i)=><mesh key={i} position={[-.22+i*.11,.75,0]} rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.345,.345,.025,24]}/><meshStandardMaterial color="#3b7a83" metalness={.7}/></mesh>)}
 <mesh position={[-.61,.79,0]} rotation={[Math.PI/2,0,0]} castShadow><cylinderGeometry args={[.38,.38,.23,32]}/><meshStandardMaterial color="#517c88" metalness={.75} roughness={.3}/></mesh>
 <BoltRing position={[-.61,.79,.13]} radius={.29} rotation={[Math.PI/2,0,0]}/>
 <CylinderBetween a={[-.7,.8,0]} b={[-1.0,.8,0]} radius={.11}/><CylinderBetween a={[-.52,.97,0]} b={[-.52,1.15,0]} radius={.1}/>
 <mesh position={[.25,1.13,0]}><boxGeometry args={[.33,.12,.28]}/><meshStandardMaterial color="#273f4d" metalness={.5}/></mesh>
 <mesh position={[.25,1.2,0]}><boxGeometry args={[.2,.015,.13]}/><meshBasicMaterial color={running?colors.teal:'#6e7d85'}/></mesh>
 <group ref={fan} position={[.6,.75,0]}>{[0,Math.PI/2].map(r=><mesh key={r} rotation={[r,0,0]}><boxGeometry args={[.04,.5,.06]}/><meshStandardMaterial color="#192c39"/></mesh>)}</group>
 </group>}
function Filter({alarmed}:{alarmed:boolean}){return <group position={[1.2,0,0]}>
 {[-.44,.44].map(x=><mesh key={x} position={[x,.4,0]} castShadow><boxGeometry args={[.1,.65,.55]}/><meshStandardMaterial color="#415969" metalness={.7}/></mesh>)}
 <mesh position={[0,1.77,0]} castShadow><cylinderGeometry args={[.64,.64,2.25,48]}/><meshStandardMaterial color={alarmed?'#806052':'#70929e'} metalness={.8} roughness={.32}/></mesh>
 <mesh position={[0,2.89,0]} scale={[1,.33,1]} castShadow><sphereGeometry args={[.64,40,20,0,Math.PI*2,0,Math.PI/2]}/><meshStandardMaterial color={alarmed?'#806052':'#70929e'} metalness={.8} roughness={.32}/></mesh>
 <mesh position={[0,.64,0]} scale={[1,.35,1]} rotation={[Math.PI,0,0]}><sphereGeometry args={[.64,32,16,0,Math.PI*2,0,Math.PI/2]}/><meshStandardMaterial color="#577b8c" metalness={.8}/></mesh>
 {[.7,2.8].map(y=><BoltRing key={y} position={[0,y,0]} radius={.67}/>)}
 <mesh position={[0,1.8,.647]}><boxGeometry args={[.42,.7,.025]}/><meshStandardMaterial color="#142c3b"/></mesh>
 {[0,1,2].map(i=><mesh key={i} position={[-.13+i*.13,1.8,.67]}><boxGeometry args={[.045,.45,.02]}/><meshStandardMaterial color={alarmed?colors.warning:colors.teal} emissive={alarmed?colors.alarm:colors.teal} emissiveIntensity={.2}/></mesh>)}
 <CylinderBetween a={[0,3.05,0]} b={[0,3.3,0]} radius={.04}/><mesh position={[0,3.35,0]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.13,.13,.06,24]}/><meshStandardMaterial color="#d0dce2" metalness={.6}/></mesh>
 </group>}
function Valve({x,opening}:{x:number;opening:number}){return <group position={[x,1.05,0]}>
 <mesh rotation={[0,0,Math.PI/2]} castShadow><cylinderGeometry args={[.19,.19,.3,24]}/><meshStandardMaterial color="#7ba0a9" metalness={.8} roughness={.25}/></mesh>
 {[-.19,.19].map(xx=><mesh key={xx} position={[xx,0,0]} rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.22,.22,.045,20]}/><meshStandardMaterial color="#a4bdc6" metalness={.8}/></mesh>)}
 <CylinderBetween a={[0,.12,0]} b={[0,.56,0]} radius={.04}/>
 <group position={[0,.6,0]} rotation={[0,opening/100*Math.PI*2,0]}><mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[.25,.032,8,32]}/><meshStandardMaterial color={opening<15?colors.alarm:'#4cbdc3'} metalness={.6}/></mesh>{[0,Math.PI/2].map(a=><mesh key={a} rotation={[0,a,0]}><boxGeometry args={[.46,.025,.025]}/><meshStandardMaterial color="#5cc6c9" metalness={.6}/></mesh>)}</group>
 </group>}
function Gauge({position}:{position:V3}){return <group position={position}><CylinderBetween a={[0,0,0]} b={[0,.42,0]} radius={.025}/><mesh position={[0,.48,0]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.11,.11,.07,24]}/><meshStandardMaterial color="#e4edf0" metalness={.5}/></mesh><mesh position={[0,.48,.04]} rotation={[0,0,-.55]}><boxGeometry args={[.015,.12,.012]}/><meshBasicMaterial color="#233949"/></mesh></group>}
function CameraRig({selectedId,command,controls,motion}:{selectedId:string|null;command:string;controls:React.MutableRefObject<any>;motion:React.MutableRefObject<boolean>}){const {camera,size}=useThree();const target=useRef(new THREE.Vector3(0,1,0)),destination=useRef(new THREE.Vector3(2,7,13));const moving=motion
 useEffect(()=>{if(command.startsWith('focus')&&selectedId&&positions[selectedId]){const p=positions[selectedId];target.current.set(p[0],p[1],p[2]);destination.current.set(p[0]+4.2,p[1]+3.0,p[2]+5.0)}else if(command.startsWith('top')){target.current.set(0,.8,0);destination.current.set(0,15*Math.max(1,1.95/(size.width/size.height)),.01)}else{target.current.set(0,1,0);destination.current.set(2,7,13).multiplyScalar(Math.max(1,1.95/(size.width/size.height)))}moving.current=true},[command,size.width,size.height])
 useFrame((_,delta)=>{if(!moving.current||!controls.current)return;camera.position.lerp(destination.current,Math.min(delta*4,1));controls.current.target.lerp(target.current,Math.min(delta*4,1));controls.current.update();if(camera.position.distanceTo(destination.current)<.015)moving.current=false})
 return null}
function PlantWorld({state,selectedId,onSelect,onFocus,highlightedIds,labels,flowVisible,command}:{state:State|null;selectedId:string|null;onSelect:(id:string)=>void;onFocus:(id:string)=>void;highlightedIds:string[];labels:boolean;flowVisible:boolean;command:string}){
 const controls=useRef<any>(null),motion=useRef(false),v=state?.values,c=state?.controls; const delivery=v?.delivery_m3h??v?.flow_m3h??0; const flow=delivery+(v?.leak_m3h??0)
 const alarms=new Set(state?.alarms.map(a=>a.asset_id)||[]), hi=new Set(highlightedIds)
 const running=(id:string)=>state?.equipment[id]?.status==='running'
 const equip=(id:string,children:React.ReactNode)=><Equipment key={id} id={id} selected={selectedId===id} highlighted={hi.has(id)} alarmed={alarms.has(id)} onSelect={onSelect} onFocus={onFocus}>{children}</Equipment>
 return <>
 <color attach="background" args={['#101c29']}/><fog attach="fog" args={['#101c29',22,48]}/><ambientLight intensity={.9}/><hemisphereLight args={['#c2e3ee','#132333',1.5]}/><directionalLight position={[0,12,5]} intensity={2.8} castShadow shadow-mapSize={[1024,1024]} shadow-camera-left={-12} shadow-camera-right={12} shadow-camera-top={10} shadow-camera-bottom={-10}/><pointLight position={[-3,3,-5]} color="#52a4cc" intensity={22}/>
 <mesh rotation={[-Math.PI/2,0,0]} receiveShadow position={[0,-.05,0]}><planeGeometry args={[100,100]}/><meshStandardMaterial color="#101c29" roughness={1}/></mesh>
 <gridHelper args={[40,40,'#21394a','#192c3c']} position={[0,-.035,0]}/>
 <mesh position={[.3,.025,0]} receiveShadow><boxGeometry args={[15.4,.15,6.4]}/><meshStandardMaterial color="#203443" metalness={.25} roughness={.8}/></mesh>
 <Line points={[[-7.35,.12,-3.15],[7.95,.12,-3.15],[7.95,.12,3.15],[-7.35,.12,3.15],[-7.35,.12,-3.15]]} color="#3d6579" lineWidth={1}/>
 {[-6,-3,0,3,6].map(x=><mesh key={x} position={[x,.11,0]}><boxGeometry args={[.025,.01,6.1]}/><meshStandardMaterial color="#294351"/></mesh>)}
 <Pipe points={[[-3.9,.8,0],[-3.6,.8,0]]} flow={flow} lit={hi.has('T-101')} enabled={flowVisible} playing={!!state?.playing}/>
 {[-1.55,1.55].map((z,i)=><group key={z}><Pipe points={[[-3.6,.8,0],[-3.6,.8,z],[-3.35,.8,z]]} flow={running(i===0?'P-101A':'P-101B')?flow:0} lit={hi.has(i===0?'P-101A':'P-101B')} enabled={flowVisible} playing={!!state?.playing}/><Pipe points={[[-2.92,1.15,z],[-.7,1.15,z],[-.7,1.05,0]]} flow={running(i===0?'P-101A':'P-101B')?flow:0} lit={hi.has(i===0?'P-101A':'P-101B')} enabled={flowVisible} playing={!!state?.playing}/></group>)}
 <Pipe points={[[-.7,1.05,0],[.56,1.05,0]]} flow={flow} lit={hi.has('F-101')} enabled={flowVisible} playing={!!state?.playing}/>
 <Pipe points={[[1.84,1.05,0],[3.3,1.05,0],[4.15,1.05,0]]} flow={flow} lit={hi.has('F-101')||hi.has('V-101')} enabled={flowVisible} playing={!!state?.playing}/>
 <Pipe points={[[4.15,1.05,0],[4.9,1.05,0],[6.65,1.05,0],[6.65,.45,0]]} flow={delivery} lit={hi.has('V-101')||hi.has('V-102')} enabled={flowVisible} playing={!!state?.playing}/>
 {equip('T-101',<Tank level={v?.tank_level_m??4}/>)}
 {equip('P-101A',<Pump z={-1.55} running={running('P-101A')} speed={c?.pump_speed_pct??0} playing={!!state?.playing}/>)}
 {equip('P-101B',<Pump z={1.55} running={running('P-101B')} speed={c?.pump_speed_pct??0} playing={!!state?.playing}/>)}
 {equip('F-101',<Filter alarmed={alarms.has('F-101')}/>)}
 {equip('V-101',<Valve x={3.3} opening={c?.valve_open_pct??100}/>)}
 {equip('V-102',<Valve x={4.9} opening={c?.outlet_open===false?0:100}/>)}
 <Gauge position={[-.05,1.05,0]}/><Gauge position={[2.45,1.05,0]}/>
 <mesh position={[5.8,1.05,0]} rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.15,.15,.25,20]}/><meshStandardMaterial color="#5c9ba8" metalness={.65}/></mesh>
 <mesh position={[5.8,1.28,0]}><boxGeometry args={[.24,.17,.2]}/><meshStandardMaterial color="#234251"/></mesh>
 {v&&v.leak_m3h>.01&&<group position={[4.15,.65,0]}>{[0,1,2,3,4].map(i=><mesh key={i} position={[Math.sin(i*2.4)*.15,.1+i*.07,Math.cos(i*2.4)*.15]}><sphereGeometry args={[.04,8,8]}/><meshBasicMaterial color={colors.blue}/></mesh>)}<mesh position={[0,-.47,0]} rotation={[-Math.PI/2,0,0]}><circleGeometry args={[.4,24]}/><meshBasicMaterial color="#2686a8" transparent opacity={.5}/></mesh></group>}
 <ContactShadows position={[0,.13,0]} opacity={.32} scale={22} blur={2.5} far={8} resolution={256} color="#000000"/>
 <OrbitControls ref={controls} onStart={()=>{motion.current=false}} makeDefault target={[0,1,0]} minDistance={4} maxDistance={45} maxPolarAngle={Math.PI/2.05} enableDamping dampingFactor={.08}/><CameraRig selectedId={selectedId} command={command} controls={controls} motion={motion}/>
 </>
}
const overlayButton:React.CSSProperties={border:'1px solid #344a5b',background:'rgba(15,28,41,.93)',color:'#b8cbd8',padding:'7px 10px',borderRadius:6,cursor:'pointer',fontSize:10,fontFamily:'inherit'}
export default function TwinScene({plant,state,selectedId,onSelect,highlightedIds=[],showLabels=true,onTrace,onAskAI,onTestIntervention}:Props){
 const [labels,setLabels]=useState(showLabels),[flowVisible,setFlowVisible]=useState(true),[command,setCommand]=useState('overview-0')
 const [failed,setFailed]=useState(false)
 const labelElements=useRef<Record<string,HTMLButtonElement|null>>({})
 useEffect(()=>setLabels(showLabels),[showLabels])
 const v=state?.values,c=state?.controls
 const highDP=!!state?.alarms.some(a=>a.asset_id==='F-101')
 const focus=(id:string)=>{onSelect(id);setCommand('focus-'+Date.now())}
 const labelValue=(id:string)=>!v||!c?'Awaiting solver':id==='T-101'?`${v.tank_level_m.toFixed(1)} m · ${v.tank_level_pct.toFixed(0)}%`:id==='F-101'?`ΔP ${v.filter_dp_bar.toFixed(2)} bar`:id==='V-101'?`${c.valve_open_pct.toFixed(0)}% open`:id==='V-102'?(c.outlet_open?'Open':'Closed'):`${state?.equipment[id]?.status==='running'?c.pump_speed_pct.toFixed(0):'0'}% speed`
 const webgl=useMemo(()=>{try{const c=document.createElement('canvas');return !!(c.getContext('webgl2')||c.getContext('webgl'))}catch{return false}},[])
 return <div className="twin-canvas-wrap" style={{position:'relative',height:'100%',minHeight:320,width:'100%',overflow:'hidden',background:'#101c29'}}>

 {!webgl||failed?<div style={{height:'100%',display:'grid',placeItems:'center',padding:32,textAlign:'center',color:'#a6becd'}}>3D graphics are unavailable in this browser. Use the process graph and schematic to investigate the same model.</div>:<Canvas shadows camera={{position:[2,7,13],fov:34,near:.1,far:100}} dpr={[1,1.7]} gl={{antialias:true,powerPreference:'high-performance'}} onCreated={({gl})=>{gl.toneMapping=THREE.ACESFilmicToneMapping;gl.toneMappingExposure=1.15;gl.domElement.addEventListener('webglcontextlost',()=>setFailed(true))}}><Suspense fallback={null}><PlantWorld state={state} selectedId={selectedId} onSelect={onSelect} onFocus={focus} highlightedIds={highlightedIds} labels={labels} flowVisible={flowVisible} command={command}/><LabelProjector elements={labelElements} selectedId={selectedId} state={state}/></Suspense></Canvas>}
 <div style={{position:'absolute',left:18,top:49,zIndex:2,display:'flex',alignItems:'center',gap:12,padding:'7px 10px',border:'1px solid #315062',borderRadius:6,background:'#0c1c29df',color:'#8ba8b9',fontSize:9,pointerEvents:'none'}}><span style={{display:'flex',alignItems:'center',gap:6}}><span style={{width:5,height:5,borderRadius:'50%',background:state?.playing?colors.teal:colors.warning}}/>{state?.playing?'OPERATING STATE':'PAUSED SNAPSHOT'}</span><b style={{color:colors.teal,fontSize:12,fontVariantNumeric:'tabular-nums'}}>{v?.delivery_m3h.toFixed(1)??'—'} <small style={{fontSize:8,fontWeight:400}}>m³/h →</small></b></div>
 {labels&&<div style={{position:'absolute',inset:0,pointerEvents:'none',overflow:'hidden'}}>{Object.keys(labelPositions).map(id=>{const alarmed=state?.alarms.some(a=>a.asset_id===id),color=alarmed?colors.alarm:selectedId===id?colors.blue:colors.teal,filterDetail=id==='F-101'&&(selectedId===id||highDP);return <button key={id} ref={element=>{labelElements.current[id]=element}} data-testid={`twin-label-${id}`} title={`${id} · ${state?.equipment[id]?.status??'Awaiting solver'} · click to inspect; double click to focus`} onClick={()=>onSelect(id)} onDoubleClick={()=>focus(id)} style={{...labelBase,width:filterDetail?126:74,position:'absolute',left:0,top:0,opacity:0,pointerEvents:'auto',borderColor:color+'90',textAlign:'left',zIndex:2}}><span style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}><b style={{fontSize:10,letterSpacing:'.015em',whiteSpace:'nowrap'}}>{id}</b><span style={{fontSize:7,color}}>{alarmed?(id==='F-101'?'HIGH ΔP':'ALARM'):state?.equipment[id]?.status==='standby'?'STBY':'●'}</span></span>{filterDetail&&v?<span style={{display:'block',fontSize:8,lineHeight:1.6,color:'#a5bdcc',fontVariantNumeric:'tabular-nums',marginTop:3}}><span style={{display:'flex',justifyContent:'space-between'}}><span>PT-101 inlet</span><b>{v.pt101_bar.toFixed(2)} bar</b></span><span style={{display:'flex',justifyContent:'space-between'}}><span>PT-102 outlet</span><b>{v.pt102_bar.toFixed(2)} bar</b></span><span style={{display:'flex',justifyContent:'space-between',borderTop:'1px solid #35505c',marginTop:2,paddingTop:2,color}}><span>Filter ΔP</span><b>{v.filter_dp_bar.toFixed(2)} bar</b></span></span>:<span style={{display:'block',marginTop:2,fontSize:8,color:'#a5bdcc',whiteSpace:'nowrap',fontVariantNumeric:'tabular-nums'}}>{labelValue(id)}</span>}</button>})}</div>}
 <div style={{position:'absolute',top:16,right:16,zIndex:2,display:'flex',gap:5}}><button style={overlayButton} onClick={()=>setCommand('overview-'+Date.now())} title="Overview camera">Overview</button><button style={overlayButton} onClick={()=>setCommand('top-'+Date.now())} title="Top view">Top</button><button style={{...overlayButton,opacity:selectedId?1:.4}} disabled={!selectedId} onClick={()=>selectedId&&focus(selectedId)}>Focus asset</button></div>
 <div style={{position:'absolute',top:53,right:16,zIndex:2,display:'flex',gap:5}}><button style={{...overlayButton,fontSize:9,padding:'5px 8px',color:labels?colors.teal:'#7b94a5'}} onClick={()=>setLabels(!labels)}>Labels {labels?'on':'off'}</button><button style={{...overlayButton,fontSize:9,padding:'5px 8px',color:flowVisible?colors.teal:'#7b94a5'}} onClick={()=>setFlowVisible(!flowVisible)}>Flow arrows {flowVisible?'on':'off'}</button></div>
 <div style={{position:'absolute',bottom:13,left:16,right:16,zIndex:3,display:'flex',flexWrap:'wrap',alignItems:'center',justifyContent:'space-between',gap:7,padding:'9px 10px',border:'1px solid #315062',borderRadius:7,background:'rgba(10,25,37,.96)',boxShadow:'0 4px 15px #0003'}}><div style={{display:'flex',alignItems:'center',gap:8}}><span style={{width:5,height:5,borderRadius:'50%',background:highDP?colors.warning:colors.teal}}/><b style={{fontSize:10,color:'#e3edf3'}}>{selectedId??'SELECT EQUIPMENT'}</b><span style={{fontSize:8,color:'#7e9eaf'}}>3D INVESTIGATION</span></div><div style={{display:'flex',gap:5,flexWrap:'wrap'}}><button style={overlayButton} disabled={!selectedId||!onTrace} onClick={()=>onTrace?.('upstream')}>↖ Upstream</button><button style={overlayButton} disabled={!selectedId||!onTrace} onClick={()=>onTrace?.('downstream')}>↘ Downstream</button><button style={{...overlayButton,color:'#89e5d4'}} disabled={!selectedId||!onAskAI} onClick={()=>selectedId&&onAskAI?.(selectedId)}>✦ Ask AI</button><button style={{...overlayButton,color:'#a4d9f1'}} disabled={!selectedId||!onTestIntervention} onClick={()=>selectedId&&onTestIntervention?.(selectedId)}>Test intervention ↗</button></div></div>
 <div style={{position:'absolute',bottom:68,right:18,color:'#7892a5',fontSize:8,zIndex:2,pointerEvents:'none'}}>Drag to orbit · Scroll to zoom · Double-click equipment to focus</div>

 </div>
}
