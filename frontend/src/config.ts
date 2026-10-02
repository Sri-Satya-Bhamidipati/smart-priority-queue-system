import type {ContextInfo,NewCustomer} from './types'

export interface Ctx extends ContextInfo{id:string;label:string;icon:string;desc:string;accent:string;motif:string;urgencies:string[];services:string[]}

const PRESENTATION:Record<string,{label:string;icon:string;desc:string;accent:string;motif:string}>={
	HOSPITAL:{label:'Hospital OPD',icon:'🏥',desc:'Prioritize patients based on urgency and waiting time.',accent:'#71856A',motif:'🌿'},
	BANK:{label:'Banking Service',icon:'🏦',desc:'Keep customer service moving while handling urgent requests.',accent:'#5A3E32',motif:'☕'},
	GOVERNMENT:{label:'Government Office',icon:'🏛️',desc:'Manage citizen requests with transparent prioritization.',accent:'#B85C4A',motif:'📄'},
	COLLEGE:{label:'College Administration',icon:'🎓',desc:'Organize student services and administrative requests.',accent:'#B8794B',motif:'📓'}
}

export const mapContexts=(items:ContextInfo[]):Ctx[]=>items.map(context=>{
	const presentation=PRESENTATION[context.name]??{label:context.name,icon:'•',desc:'Context-specific service queue.',accent:'#B8794B',motif:''}
	return{id:context.name,label:presentation.label,icon:presentation.icon,desc:presentation.desc,accent:presentation.accent,motif:presentation.motif,...context,urgencies:Object.keys(context.urgency_scores),services:Object.keys(context.service_types)}
})

export const demoCustomers=(context:Ctx):NewCustomer[]=>{
	const timestamp=Date.now()
	const suffix=Math.random().toString(36).slice(2,7).toUpperCase()
	return Array.from({length:6},(_,index)=>({
		customer_id:`DEMO-${context.id}-${timestamp}-${suffix}-${index+1}`,
		urgency:context.urgencies[index%context.urgencies.length],
		service_type:context.services[index%context.services.length],
		estimated_service_time:5+index*3,
		arrival_time:new Date().toISOString()
	}))
}
