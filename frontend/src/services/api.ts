import type {ComparisonResponse,ContextInfo,Customer,Metrics,NewCustomer} from '../types'
export const BASE=import.meta.env.VITE_API_URL??'http://localhost:8000'
export class ApiError extends Error{constructor(message:string,public readonly kind:'unavailable'|'api',public readonly status?:number){super(message);this.name='ApiError'}}
async function req<T>(path:string,init?:RequestInit):Promise<T>{
  let r:Response
  try{r=await fetch(BASE+path,{headers:{'Content-Type':'application/json'},...init})}
  catch{throw new ApiError(`Cannot reach backend at ${BASE}`,'unavailable')}
  if(!r.ok){let d='';try{const j=await r.json();d=typeof j.detail==='string'?j.detail:JSON.stringify(j.detail)}catch{}throw new ApiError(d||`Backend error (${r.status})`,'api',r.status)}
  return r.json()
}
const post=(b?:unknown)=>({method:'POST',body:b===undefined?undefined:JSON.stringify(b)})
const withContext=(path:string,context:string)=>`${path}?context=${encodeURIComponent(context)}`
export const api={
  contexts:async():Promise<ContextInfo[]>=>{const result=await req<{contexts:ContextInfo[]}>('/api/contexts');return result.contexts},
  add:(context:string,customer:NewCustomer):Promise<Customer>=>req('/api/queue/add',post({...customer,context})),
  batch:(context:string,customers:NewCustomer[])=>req('/api/queue/batch',post({context,customers})),
  queue:async(context:string):Promise<Customer[]>=>{const result=await req<{context:string;queue:Customer[]}>(withContext('/api/queue',context));if(result.context!==context)throw new ApiError(`Backend returned ${result.context} queue data for ${context}.`,'api');return result.queue},
  next:(context:string):Promise<Customer|null>=>req(withContext('/api/queue/next',context)),
  serve:(context:string):Promise<Customer|null>=>req(withContext('/api/queue/serve',context),post()),
  metrics:async(context:string):Promise<Metrics>=>{const result=await req<Metrics>(withContext('/api/queue/metrics',context));if(result.context!==context)throw new ApiError(`Backend returned ${result.context} metrics for ${context}.`,'api');return result},
  reset:(context:string)=>req(withContext('/api/queue/reset',context),post()),
  compare:async(context:string,customers:Customer[]):Promise<ComparisonResponse>=>{const result=await req<ComparisonResponse>('/api/queue/compare',post({context,customers:customers.map(({customer_id,arrival_time,urgency,service_type,estimated_service_time})=>({customer_id,arrival_time,urgency,service_type,estimated_service_time}))}));if(result.context!==context)throw new ApiError(`Backend returned ${result.context} comparison for ${context}.`,'api');return result},
}
