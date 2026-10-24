import { memo, useMemo } from 'react';
import { ReactFlow, Background, Controls as GraphControls, Handle, Position, MarkerType, type NodeProps } from '@xyflow/react';
import { Droplets, Gauge, Filter, Cylinder, CircleDot, ArrowUpRight, Waves, Radio, GitBranch } from 'lucide-react';
import type { Plant, State } from '../types';
import '@xyflow/react/dist/style.css';

const positions: Record<string, {x:number;y:number}> = {
  'T-101': {x:25,y:230}, 'J-SUCTION':{x:235,y:275}, 'P-101A':{x:300,y:110},
  'P-101B':{x:300,y:350}, 'J-DISCHARGE':{x:510,y:275}, 'F-101':{x:590,y:230},
  'V-101':{x:810,y:230},'V-102':{x:1010,y:230},'OUTLET':{x:1210,y:230},
  'LT-101':{x:35,y:55},'PT-101':{x:525,y:55},'PT-102':{x:750,y:55},'FT-101':{x:1040,y:470},
};
const assetIcons: Record<string, typeof Cylinder> = {tank:Cylinder,pump:CircleDot,filter:Filter,valve:Gauge,outlet:ArrowUpRight,junction:GitBranch};
export function assetReading(id:string, state:State|null): {value:string;unit:string;label:string} {
  const v=state?.values;
  if (!v) return {value:'—',unit:'',label:'Waiting for solver'};
  if(id==='T-101') return {value:v.tank_level_pct.toFixed(1),unit:'%',label:'Storage level'};
  if(id.startsWith('P-101')) return {value:(state?.equipment[id]?.value??0).toFixed(0),unit:'%',label:state?.equipment[id]?.status==='running'?'Drive speed':state?.equipment[id]?.status==='tripped'?'Low-level interlock':state?.controls.active_pump===id?'Drive stopped':'Standby available'};
  if(id==='F-101') return {value:v.filter_dp_bar.toFixed(2),unit:'bar',label:'Differential pressure'};
  if(id==='V-101') return {value:v.valve_open_pct.toFixed(0),unit:'%',label:'Valve opening'};
  if(id==='V-102') return {value:state?.controls.outlet_open?'OPEN':'CLOSED',unit:'',label:'Isolation state'};
  return {value:v.delivery_m3h.toFixed(1),unit:'m³/h',label:'Delivered flow'};
}
const EquipmentNode=memo(({data,selected}:NodeProps)=>{
  const d=data as any;
  if(d.type==='junction') return <div className={`junction-node ${d.highlight?'path-active':''}`}><Handle type="target" position={Position.Left}/><Handle type="source" position={Position.Right}/><span/></div>;
  if(d.type==='sensor') return <div className={`sensor-node ${d.highlight?'path-active':''}`}><Handle type="source" position={Position.Bottom}/><Radio size={12}/><span>{d.tag}</span><strong>{d.reading}</strong></div>;
  const Icon=assetIcons[d.type]||CircleDot;
  return <div className={`equipment-node ${selected?'is-selected':''} ${d.alarm?'has-alarm':''} ${d.highlight?'path-active':''} ${d.inactive?'is-standby':''}`}>
    <Handle type="target" position={Position.Left}/><Handle type="source" position={Position.Right}/>
    <div className="node-top"><span className="node-icon"><Icon size={21} strokeWidth={1.6}/></span><span className={`tiny-dot ${d.alarm?'amber':d.inactive?'muted':'mint'}`}/></div>
    <div className="node-tag">{d.tag}</div><div className="node-name">{d.name}</div>
    <div className="node-reading"><strong>{d.reading.value}</strong><span>{d.reading.unit}</span></div>
    <div className="node-caption">{d.reading.label}</div>
    {d.alarm&&<div className="node-alarm">ATTENTION REQUIRED</div>}
  </div>;
});
const nodeTypes={equipment:EquipmentNode};
export default function ProcessGraph({plant,state,selectedId,onSelect,highlightedIds=[],instrumentation=true}:{plant:Plant;state:State|null;selectedId:string|null;onSelect:(id:string)=>void;highlightedIds?:string[];instrumentation?:boolean}){
 const nodes=useMemo(()=>{
   const list=plant.assets.filter(a=>instrumentation||String(a.type)!=='sensor').map((a,i)=>({id:a.id,type:'equipment',position:(plant.id==='atlas-station-01'||state)?positions[a.id]||{x:80+(i%5)*235,y:180+Math.floor(i/5)*230}:((a as any).bbox||a.source_bbox)?{x:((a as any).bbox||a.source_bbox)[0]*1800,y:((a as any).bbox||a.source_bbox)[1]*1100}:{x:80+(i%5)*235,y:180+Math.floor(i/5)*230},selected:a.id===selectedId,data:{tag:a.id,name:a.name,type:a.type,reading:String(a.type)==='sensor'?(state?(a.id==='PT-101'?`${state.values.pt101_bar.toFixed(2)} bar`:a.id==='PT-102'?`${state.values.pt102_bar.toFixed(2)} bar`:a.id==='LT-101'?`${state.values.tank_level_m.toFixed(2)} m`:`${state.values.delivery_m3h.toFixed(1)} m³/h`):'UNMAPPED'):assetReading(a.id,state),alarm:state?.alarms.some(x=>x.asset_id===a.id),highlight:highlightedIds.includes(a.id),inactive:a.type==='pump'&&state?.controls.active_pump!==a.id}}));
   if(instrumentation) for(const sensor of plant.sensors){
    if(plant.assets.some(a=>a.id===sensor.id))continue;
    let pos={x:600,y:30},val='—';
    if(sensor.id==='LT-101'){pos={x:35,y:55};val=state?`${state.values.tank_level_m.toFixed(2)} m`:'—';}
    if(sensor.id==='PT-101'){pos={x:525,y:55};val=state?`${state.values.pt101_bar.toFixed(2)} bar`:'—';}
    if(sensor.id==='PT-102'){pos={x:750,y:55};val=state?`${state.values.pt102_bar.toFixed(2)} bar`:'—';}
    if(sensor.id==='FT-101'){pos={x:1040,y:470};val=state?`${state.values.delivery_m3h.toFixed(1)} m³/h`:'—';}
    list.push({id:sensor.id,type:'equipment',position:pos,selected:false,data:{type:'sensor',tag:sensor.id,reading:val,name:sensor.label,alarm:false,highlight:false,inactive:false} as any});
   }
   return list;
 },[plant,state,selectedId,highlightedIds,instrumentation]);
 const edges=useMemo(()=>{
 const standby = state?.controls.active_pump==='P-101A'?'P-101B':'P-101A';
 const isInactive = (c:{from:string;to:string}) => !!state && (c.from===standby || c.to===standby);

   const list=plant.connections.filter(c=>c.kind==='process'||instrumentation).map(c=>({id:c.id,source:c.from,target:c.to,type:'smoothstep',animated:c.kind==='process'&&!isInactive(c)&&!!state&&(state.values.flow_m3h+state.values.leak_m3h)>.1&&state.playing,label:c.label||'',style:{stroke:highlightedIds.includes(c.from)&&highlightedIds.includes(c.to)?'#70f1c8':isInactive(c)?'#30475a':'#39718b',strokeWidth:highlightedIds.includes(c.from)&&highlightedIds.includes(c.to)?3:c.kind==='signal'?1:2,strokeDasharray:c.kind==='signal'?'5 5':undefined},markerEnd:{type:MarkerType.ArrowClosed,color:'#61bed2',width:14,height:14},labelStyle:{fill:'#8aa7bc',fontSize:10},labelBgStyle:{fill:'#0c1726',fillOpacity:.9}}));
   if(instrumentation)for(const s of plant.sensors)if(!plant.connections.some(c=>c.kind==='signal'&&(c.from===s.id||c.to===s.id)))list.push({id:`signal-${s.id}`,source:s.id,target:s.asset_id,type:'smoothstep',animated:false,label:'',style:{stroke:'#526279',strokeWidth:1,strokeDasharray:'5 5'} as any,markerEnd:{type:MarkerType.ArrowClosed,color:'#526279',width:8,height:8},labelStyle:{fill:'#8aa7bc',fontSize:10},labelBgStyle:{fill:'#0c1726',fillOpacity:.9}});
   return list;
 },[plant,state,highlightedIds,instrumentation]);
 return <div className="process-graph" data-testid="process-graph"><ReactFlow key={plant.id} nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodeClick={(_,n)=>onSelect(plant.sensors.find(s=>s.id===n.id)?.asset_id||n.id)} fitView fitViewOptions={{padding:.16}} minZoom={.3} maxZoom={1.7} nodesDraggable={false} nodesConnectable={false} attributionPosition="bottom-left" proOptions={{hideAttribution:true}}><Background color="#26374b" gap={22} size={1}/><GraphControls showInteractive={false}/></ReactFlow>{(plant.id==='atlas-station-01'||!!state)?<><div className="graph-section-label storage"><span>01</span> STORAGE</div><div className="graph-section-label pumping"><span>02</span> DUTY / STANDBY</div><div className="graph-section-label treatment"><span>03</span> FILTRATION & DELIVERY</div></>:<div className="graph-section-label storage"><span>AI</span> SOURCE-ALIGNED TOPOLOGY · REVIEW REQUIRED</div>}<div className="graph-legend"><span><i className="legend-line"/>Process connection</span><span><i className="legend-line dashed"/>Instrumentation</span><span><i className="tiny-dot mint"/>Operational</span><span><i className="tiny-dot amber"/>Attention</span></div></div>;
}
