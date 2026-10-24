// Recording assertions describe the actual API responses. They never change the
// application provider, model, requests, UI branding, or displayed measurements.
export const expectedProvider=process.env.EXPECTED_AI_PROVIDER||'gemma';
export const expectedModel=process.env.EXPECTED_AI_MODEL||'';
export const providerTitle=expectedProvider==='anthropic'?'Claude':expectedProvider==='gemma'?'Gemma':expectedProvider;
export const screenshotPrefix=expectedProvider==='anthropic'?'claude-backup-':'';
export const recordedModels=new Set();
if(expectedProvider==='anthropic'&&!expectedModel)throw Error('Set EXPECTED_AI_MODEL to the actual isolated Claude server model before recording.');
export function assertAIIdentity(result,stage){
 const actualProvider=result.source||result.provider;
 if(actualProvider!==expectedProvider)throw Error(`${stage}: actual provider ${actualProvider} differs from expected ${expectedProvider}`);
 if(typeof result.model!=='string'||!result.model)throw Error(`${stage}: API omitted actual model identity`);
 if(expectedModel&&result.model!==expectedModel)throw Error(`${stage}: actual model ${result.model} differs from expected ${expectedModel}`);
 if(!expectedModel&&expectedProvider==='gemma'&&!result.model.startsWith('gemma-4-'))throw Error(`${stage}: expected a Gemma4 response, received ${result.model}`);
 recordedModels.add(result.model);
 console.log(`Verified ${stage}: ${actualProvider} / ${result.model}`);
}
export function recordingMetadata(scope,live){return{recorded_at:new Date().toISOString(),scope,live_ai:live,ai_provider:live?expectedProvider:null,ai_models:[...recordedModels],classification:expectedProvider==='anthropic'?'Explicit Claude backup recording from an isolated server. The main application remains Gemma.':'Gemma application recording.',evidence:'Real browser, image extraction, reviewed topology, hydraulic solver, AI responses and isolated what-if requests; no mocked responses or relabeled provider.'}}
