import {useCallback,useEffect,useRef,useState,ReactNode} from 'react'
import {LineChart,Line,BarChart,Bar,XAxis,YAxis,Tooltip,CartesianGrid,Legend,Label,ResponsiveContainer} from 'recharts'
import {api,ApiError} from './services/api'
import {demoCustomers,mapContexts,Ctx} from './config'
import type {ComparisonResponse,Customer,Metrics,NewCustomer} from './types'

type Page='queue'|'perf'|'how'
const NAV:[Page,string][]=[['queue','Live Queue'],['perf','Performance'],['how','How Prioritization Works']]
type RequestFailure={kind:'unavailable'|'api';message:string}
const failureFor=(error:unknown):RequestFailure=>error instanceof ApiError?{kind:error.kind,message:error.message}:{kind:'api',message:error instanceof Error?error.message:'Unexpected API error.'}
const f1=(n?:number)=>n===undefined?'—':(Math.round(n*10)/10).toString()
const st=(c:Customer)=>c.status?.toUpperCase()
const hot=(u:string)=>['critical','high','emergency','urgent'].includes(u.toLowerCase())
const Mark=()=><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#B8794B" strokeWidth="1.8" strokeLinecap="round"><path d="M4 6h7M4 12h7M4 18h7M15 6h5M15 12h5M15 18h5"/><circle cx="13" cy="6" r="1" fill="#B8794B" stroke="none"/><circle cx="13" cy="12" r="1" fill="#B8794B" stroke="none"/><circle cx="13" cy="18" r="1" fill="#B8794B" stroke="none"/></svg>
const Btn=({p,...r}:any)=><button {...r} className={`btn disabled:opacity-40 ${p?'bg-coffee text-white hover:bg-ink':'border border-line bg-surface text-coffee hover:bg-cream'} ${r.className??''}`}/>

function Modal({title,close,children}:{title:string;close:()=>void;children:ReactNode}){
  const ref=useRef<HTMLDivElement>(null)
  useEffect(()=>{const prev=document.activeElement as HTMLElement|null;ref.current?.querySelector<HTMLElement>('input,button,select')?.focus()
    const k=(e:KeyboardEvent)=>e.key==='Escape'&&close();window.addEventListener('keydown',k);return()=>{window.removeEventListener('keydown',k);prev?.focus()}},[])
  return<div className="fixed inset-0 z-40 flex justify-end"><div className="absolute inset-0 bg-ink/30" onClick={close}/>
    <div ref={ref} role="dialog" aria-modal="true" aria-label={title} className="slide relative w-full max-w-sm bg-surface p-6 shadow-lift overflow-y-auto">{children}</div></div>}

export default function App(){
  const [contexts,setContexts]=useState<Ctx[]>([])
  const [contextsLoading,setContextsLoading]=useState(true)
  const [contextsError,setContextsError]=useState<RequestFailure|null>(null)
  const [ctx,setCtx]=useState<Ctx|null>(null)
  const [showCtx,setShowCtx]=useState(false)
  const [page,setPage]=useState<Page>('queue')
  const [queue,setQueue]=useState<Customer[]>([])
  const [nextCustomer,setNextCustomer]=useState<Customer|null>(null)
  const [m,setM]=useState<Metrics|null>(null)
  const [comparison,setComparison]=useState<ComparisonResponse|null>(null)
  const [comparisonError,setComparisonError]=useState<string|null>(null)
  const [hist,setHist]=useState<{t:string;len:number;avg:number}[]>([])
  const [loaded,setLoaded]=useState(false)
  const [failure,setFailure]=useState<RequestFailure|null>(null)
  const [busy,setBusy]=useState(false)
  const [toast,setToast]=useState<{k:'ok'|'err';msg:string}|null>(null)
  const [panel,setPanel]=useState(false)
  const [added,setAdded]=useState<{id:string;score:number;pos:number}|null>(null)
  const [hl,setHl]=useState('')
  const [confirm,setConfirm]=useState(false)

  const refreshSequence=useRef(0)
  const say=(k:'ok'|'err',msg:string)=>{setToast({k,msg});setTimeout(()=>setToast(null),4000)}
  const loadContexts=useCallback(async()=>{
    setContextsLoading(true);setContextsError(null)
    try{setContexts(mapContexts(await api.contexts()))}
    catch(error){setContextsError(failureFor(error))}
    finally{setContextsLoading(false)}
  },[])
  useEffect(()=>{void loadContexts()},[loadContexts])
  const refresh=useCallback(async(context:Ctx):Promise<Customer[]|null>=>{
    const sequence=++refreshSequence.current
    try{
      const [q,top,mt]=await Promise.all([api.queue(context.id),api.next(context.id),api.metrics(context.id)])
      if(sequence!==refreshSequence.current)return null
      if(mt.context!==context.id)throw new ApiError(`Backend returned ${mt.context} metrics for ${context.id}.`,'api')
      setQueue(q);setNextCustomer(top);setM(mt);setFailure(null)
      try{const result=await api.compare(context.id,q);if(sequence===refreshSequence.current){setComparison(result);setComparisonError(null)}}
      catch(error){if(sequence===refreshSequence.current){setComparison(null);setComparisonError(failureFor(error).message)}}
      if(sequence!==refreshSequence.current)return null
      setHist(h=>[...h,{t:new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}),len:mt.queue_length,avg:mt.average_waiting_time}].slice(-20))
      return q
    }catch(error){if(sequence===refreshSequence.current){setFailure(failureFor(error));setQueue([]);setNextCustomer(null);setM(null);setComparison(null)}return null}
    finally{if(sequence===refreshSequence.current)setLoaded(true)}
  },[])
  useEffect(()=>{if(ctx){void refresh(ctx);const i=setInterval(()=>void refresh(ctx),5000);return()=>{clearInterval(i);refreshSequence.current++}}},[ctx,refresh])
  const act=async(fn:()=>Promise<unknown>,msg:string)=>{setBusy(true);try{await fn();if(ctx)await refresh(ctx);say('ok',msg)}catch(error){say('err',failureFor(error).message)}finally{setBusy(false)}}
  const seed=()=>ctx&&act(()=>api.batch(ctx.id,demoCustomers(ctx)),'Demo requests added to the live queue.')

  const enter=(context:Ctx)=>{setCtx(context);setLoaded(false);setFailure(null);setQueue([]);setNextCustomer(null);setM(null);setComparison(null);setComparisonError(null);setHist([]);setPage('queue')}
  const selectContext=(context:Ctx)=>{setCtx(context);setLoaded(false);setFailure(null);setQueue([]);setNextCustomer(null);setM(null);setComparison(null);setComparisonError(null);setHist([])}
  const next=nextCustomer??undefined
  const serve=()=>{if(!ctx||!next)return;const id=next.customer_id;act(()=>api.serve(ctx.id),`${id} served successfully`)}
  const add=async(customer:NewCustomer)=>{if(!ctx)return;setBusy(true);try{const result=await api.add(ctx.id,customer);const current=await refresh(ctx);setAdded({id:result.customer_id,score:result.priority_score,pos:(current?.findIndex(item=>item.customer_id===result.customer_id)??-1)+1});setHl(result.customer_id)}catch(error){say('err',failureFor(error).message)}finally{setBusy(false)}}

  if(!ctx)return<div className="min-h-screen px-6 py-12">
    <div className="max-w-3xl mx-auto pop">
      <div className="flex items-center gap-2 text-sm font-semibold text-muted"><Mark/>Smart Queue Management System</div>
      <h1 className="font-display text-5xl text-coffee mt-6 leading-tight">Queues shouldn’t only follow arrival order.</h1>
      <div className="grid sm:grid-cols-2 gap-4 mt-8 text-sm">
        <div className="card p-5"><div className="text-xs font-bold text-terra uppercase tracking-wide">The problem</div><p className="mt-2 text-ink">Traditional queues treat people by arrival order or fixed priority. Real requests differ in urgency, waiting time, and service requirement.</p></div>
        <div className="card p-5 !border-caramel/50"><div className="text-xs font-bold text-sage uppercase tracking-wide">What this system does</div><p className="mt-2 text-ink">It prioritizes requests dynamically using those factors, and uses waiting-time aging to reduce starvation.</p></div></div>
      <div className="flex flex-wrap gap-3 mt-8"><Btn p className="!px-6 !py-3" disabled={contextsLoading||!contexts.length} onClick={()=>{const hospital=contexts.find(context=>context.id==='HOSPITAL')??contexts[0];if(hospital)enter(hospital)}}>Open Hospital Queue</Btn><Btn className="!px-6 !py-3" onClick={()=>setShowCtx(true)}>Choose Service Context</Btn></div>
      <p className="text-xs text-muted mt-3">Service contexts and request options are loaded from the live queue engine.</p>
      {contextsLoading&&<p role="status" className="text-sm text-muted mt-4">Loading service contexts…</p>}
      {contextsError&&<div className="card p-4 mt-4" role="alert"><p className="text-sm text-terra">{contextsError.kind==='unavailable'?'Queue engine unavailable':'Could not load service contexts'}: {contextsError.message}</p><Btn className="mt-3" onClick={()=>void loadContexts()}>Retry Connection</Btn></div>}
      {showCtx&&<div className="grid sm:grid-cols-2 gap-3 mt-8 pop">{contexts.map(c=><button key={c.id} disabled={contextsLoading} onClick={()=>enter(c)} className="card p-4 text-left hover:border-caramel hover:shadow-lift transition">
        <div className="font-display text-lg text-coffee">{c.icon} {c.label}</div><div className="text-sm text-muted mt-1">{c.desc}</div></button>)}</div>}
    </div></div>

  const chip=failure?[failure.kind==='unavailable'?'ENGINE OFFLINE':'API ERROR','bg-terra/15 text-terra']:loaded?['LIVE ENGINE','bg-sage/20 text-sage']:['CONNECTING…','bg-caramel/20 text-coffee']
  return<div className="min-h-screen pb-24 sm:pb-0">
    <header className="bg-surface border-b border-line px-4 sm:px-6 py-2.5 flex flex-wrap items-center gap-x-5 gap-y-2 sticky top-0 z-20">
      <div className="flex items-center gap-2"><Mark/><span className="font-display text-lg text-coffee">Smart Queue</span></div>
      <nav className="flex gap-1 overflow-x-auto order-3 sm:order-none w-full sm:w-auto">{NAV.map(([p,l])=><button key={p} onClick={()=>setPage(p)} aria-current={page===p?'page':undefined} className={`px-3 py-1.5 text-sm font-semibold rounded-md whitespace-nowrap ${page===p?'bg-coffee text-white':'text-muted hover:bg-cream'}`}>{l}</button>)}</nav>
      <div className="ml-auto flex items-center gap-3 text-sm">
        <select aria-label="Service context" className="field !w-auto !py-1.5" value={ctx.id} onChange={e=>{const selected=contexts.find(c=>c.id===e.target.value);if(selected)selectContext(selected)}}>{contexts.map(c=><option key={c.id} value={c.id}>{c.label}</option>)}</select>
        <span className={`px-2 py-1 rounded text-xs font-bold ${chip[1]}`}>{chip[0]}</span>
      </div></header>
    <main key={page} className="p-3 sm:p-5 max-w-6xl mx-auto space-y-4 pop">
      {toast&&<div role="status" className={`fixed top-16 right-4 z-50 pop rounded-lg px-4 py-2.5 shadow-lift text-sm font-semibold text-white ${toast.k==='ok'?'bg-sage':'bg-terra'}`}>{toast.k==='ok'?'✓ ':''}{toast.msg}</div>}
      {page==='queue'&&<QueueView {...{ctx,queue,next,m,loaded,failure,busy,hl}} serve={serve} openAdd={()=>{setAdded(null);setPanel(true)}} seed={seed} askReset={()=>setConfirm(true)} retry={()=>ctx?refresh(ctx):Promise.resolve(null)}/>}
      {page==='how'&&<How queue={queue} next={next} go={()=>setPage('queue')}/>}
      {page==='perf'&&<Perf {...{hist,m,comparison,comparisonError,loaded,failure}} retry={()=>ctx?refresh(ctx):Promise.resolve(null)} context={ctx}/>}
    </main>
    <div className="sm:hidden fixed bottom-0 inset-x-0 bg-surface border-t border-line p-3 flex gap-2 z-30"><Btn p className="flex-1" disabled={busy||!next} onClick={serve}>Serve Next{next?` · ${next.customer_id}`:''}</Btn><Btn onClick={()=>{setAdded(null);setPanel(true)}}>+ Add</Btn></div>
    {panel&&<Modal title="Add request" close={()=>setPanel(false)}>{added?
      <div className="space-y-4"><h2 className="font-display text-2xl text-coffee">Request added</h2>
        <div className="rounded-lg bg-cream/60 p-4 space-y-1 text-sm"><div className="font-bold text-lg text-coffee">{added.id}</div><div>Priority score (from engine): <b className="num">{f1(added.score)}</b></div><div>Queue position: <b>{added.pos?`#${added.pos}`:'—'}</b></div></div>
        <Btn p className="w-full" onClick={()=>setPanel(false)}>See it in the queue</Btn><Btn className="w-full" onClick={()=>setAdded(null)}>Add another</Btn></div>
      :<AddForm key={ctx.id} ctx={ctx} busy={busy} close={()=>setPanel(false)} onAdd={add}/>}</Modal>}
    {confirm&&<Modal title="Reset queue" close={()=>setConfirm(false)}><h2 className="font-display text-2xl text-coffee">Reset the queue?</h2><p className="text-sm text-muted mt-2">This removes every request from the queue. It can’t be undone.</p>
      <div className="flex gap-2 mt-5"><Btn className="flex-1" onClick={()=>setConfirm(false)}>Cancel</Btn><Btn p className="flex-1 !bg-terra" onClick={()=>{setConfirm(false);ctx&&act(()=>api.reset(ctx.id),'Queue reset.')}}>Reset queue</Btn></div></Modal>}
  </div>
}

function AddForm({ctx,busy,close,onAdd}:{ctx:Ctx;busy:boolean;close:()=>void;onAdd:(c:any)=>void}){
  const [f,setF]=useState({customer_id:'',urgency:ctx.urgencies[0]??'',service_type:ctx.services[0]??'',estimated_service_time:10})
  const lab='text-xs font-semibold text-muted block'
  return<form className="space-y-4" onSubmit={e=>{e.preventDefault();onAdd({...f,arrival_time:new Date().toISOString()})}}>
    <div className="flex justify-between"><div><h2 className="font-display text-2xl text-coffee">Add request</h2><p className="text-sm text-muted">The engine calculates priority and position.</p></div><button type="button" aria-label="Close" onClick={close} className="text-muted text-xl h-8">×</button></div>
    <label className={lab}>Request ID<input required className="field mt-1" value={f.customer_id} onChange={e=>setF({...f,customer_id:e.target.value})} placeholder="C108"/></label>
    <fieldset className={lab}>Urgency<div className="flex gap-1.5 mt-1">{ctx.urgencies.map(u=><button type="button" key={u} aria-pressed={f.urgency===u} onClick={()=>setF({...f,urgency:u})} className={`btn flex-1 !px-1 border ${f.urgency===u?(hot(u)?'bg-terra text-white border-terra':'bg-caramel text-white border-caramel'):'border-line text-muted'}`}>{u}</button>)}</div></fieldset>
    <label className={lab}>Service Type<select className="field mt-1" value={f.service_type} onChange={e=>setF({...f,service_type:e.target.value})}>{ctx.services.map(s=><option key={s} value={s}>{s.replace(/_/g,' ')}</option>)}</select><span className="font-normal block mt-1">Service requirement score: {ctx.service_types[f.service_type]??'—'} / 100</span></label>
    <label className={lab}>Estimated Service Time (minutes)<input type="number" min={1} required className="field mt-1" value={f.estimated_service_time} onChange={e=>setF({...f,estimated_service_time:+e.target.value})}/><span className="font-normal block mt-1">Expected service duration, used by the algorithm comparison.</span></label>
    <p className="text-xs text-muted">Arrival time is recorded automatically as now.</p>
    <Btn p disabled={busy} className="w-full !py-3">{busy?'Adding…':'Add to queue'}</Btn></form>
}

function Breakdown(){
  return<div><div className="text-xs font-bold text-muted uppercase tracking-wide mb-1">Why this request is next</div>
    <p className="text-sm text-ink">Highest dynamic priority based on urgency, waiting time, and service requirement.</p>
    <details className="mt-2 text-xs text-muted"><summary className="cursor-pointer font-semibold text-caramel">How was this score calculated?</summary><p className="mt-1">The Dynamic Priority Engine applies P = 0.50·U + 0.30·W + 0.20·S: urgency 50%, waiting 30%, and service requirement 20%. The displayed score is the total returned by the backend.</p></details></div>
}

function QueueView({ctx,queue,next,m,loaded,failure,busy,hl,serve,openAdd,seed,askReset,retry}:any){
  const mets:[string,string][]=[['Queue Length',m?String(m.queue_length):'—'],['Average Wait',m?`${f1(m.average_waiting_time)} min`:'—'],['Maximum Wait',m?`${f1(m.maximum_waiting_time)} min`:'—'],['Average Service',m?`${f1(m.average_service_time)} min`:'—'],['Throughput',m?`${m.throughput} / hr`:'—']]
  return<>
    <div><h1 className="font-display text-3xl text-coffee">Live Queue</h1><p className="text-sm text-muted">{ctx.label} · requests ordered by dynamic priority</p></div>
    {failure?<div className="card p-8 text-center border-terra/40" role="alert"><h2 className="font-display text-2xl text-terra">{failure.kind==='unavailable'?'Queue engine unavailable':'Queue API error'}</h2><p className="text-muted mt-1">{failure.message}</p>
      <div className="flex gap-2 justify-center mt-4"><Btn p onClick={retry}>Retry Connection</Btn></div></div>
    :!loaded?<div className="space-y-3"><div className="skel h-44"/><div className="skel h-56"/></div>:<>
    {next&&<section className="card !border-caramel/60 p-4 bg-caramel/5">
      <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
        <div className="min-w-0"><div className="text-xs font-bold text-caramel tracking-widest">NEXT TO SERVE · {st(next)}</div>
          <div className="font-display text-3xl sm:text-4xl text-coffee mt-1 truncate">{next.customer_id}</div>
          <div className="text-ink mt-1 font-medium">{next.service_type}</div>
          <div className="flex flex-wrap gap-x-6 gap-y-2 mt-3 text-sm"><div><div className="text-muted text-xs">Urgency</div><b className={hot(next.urgency)?'text-terra':''}>{next.urgency.toUpperCase()}</b></div><div><div className="text-muted text-xs">Waiting time</div><b className="num">{f1(next.waiting_time)} min</b></div></div>
        </div>
        <div className="sm:min-w-48 sm:border-l sm:border-line sm:pl-5"><div className="text-xs font-bold tracking-widest text-muted">PRIORITY SCORE</div><div className="font-display text-4xl sm:text-5xl leading-none text-coffee num mt-1">{f1(next.priority_score)}</div><div className="text-xs text-muted mt-2">Calculated by the Dynamic Priority Engine</div></div>
      </div>
      <div className="mt-3 pt-3 border-t border-line flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <Breakdown/>
        <Btn p disabled={busy} onClick={serve} className="!px-5 !py-2.5 w-full sm:w-auto shrink-0">Serve Next</Btn>
      </div>
    </section>}
    <section className="card p-4"><div className="flex flex-wrap items-center gap-2 mb-3"><h2 className="font-display text-xl text-coffee flex-1">Queue <span className="text-sm text-muted font-sans">({queue.length})</span></h2>
      {queue.length>0&&<Btn onClick={seed} disabled={busy}>Load demo requests</Btn>}<Btn onClick={askReset} disabled={busy||!queue.length}>Reset</Btn>{queue.length>0&&<Btn p onClick={openAdd} className="hidden sm:block">+ Add request</Btn>}</div>
      {queue.length===0?<div className="text-center py-6 sm:py-8"><div className="text-xs font-bold tracking-[.16em] text-caramel">QUEUE CLEAR</div><h3 className="font-display text-xl text-coffee mt-1">No customers are currently waiting.</h3><p className="text-sm text-muted mt-1">The Dynamic Priority Engine is ready for the next request.</p><div className="flex flex-wrap justify-center gap-2 mt-4"><Btn p onClick={openAdd}>+ Add Request</Btn><Btn onClick={seed} disabled={busy}>Load demo requests</Btn></div></div>:
      <div className="overflow-x-auto"><table className="w-full text-sm min-w-[520px]"><thead><tr className="text-left text-xs text-muted uppercase tracking-wide">{['#','Request','Service','Urgency','Wait','Priority','Status'].map(h=><th key={h} className="pb-2 pr-3 font-semibold">{h}</th>)}</tr></thead>
        <tbody>{queue.map((c:Customer,i:number)=>{const top=c.customer_id===next?.customer_id;return<tr key={c.customer_id} className={`border-t border-line ${top?'bg-caramel/10 font-semibold border-l-4 border-l-caramel':''} ${hl===c.customer_id?'flash':''}`}>
          <td className="py-2 pr-3 num text-muted">{i+1}</td><td className="pr-3 text-coffee font-bold">{c.customer_id}</td><td className="pr-3">{c.service_type}</td>
          <td className={`pr-3 ${hot(c.urgency)?'text-terra font-semibold':''}`}>{c.urgency}</td><td className="pr-3 num">{f1(c.waiting_time)} min</td><td className={`pr-3 num font-bold ${top?'text-lg text-coffee':'text-base text-coffee'}`}>{f1(c.priority_score)}</td>
          <td className={`text-xs ${top?'text-caramel font-bold':'text-muted'}`}>{st(c)}</td></tr>})}</tbody></table></div>}</section>
    <section className="grid grid-cols-2 sm:grid-cols-5 gap-px bg-line border border-line rounded-lg overflow-hidden">{mets.map(([k,v])=><div key={k} className="bg-surface px-4 py-3"><div className="num font-bold text-2xl sm:text-3xl leading-tight text-coffee">{v}</div><div className="text-xs text-muted mt-1">{k}</div></div>)}</section></>}
    </>
}

const Step=({n,t,children}:{n:number;t:string;children:ReactNode})=><section className="card p-5 flex gap-4"><div className="w-7 h-7 shrink-0 rounded bg-coffee text-white grid place-items-center text-sm font-bold">{n}</div><div className="flex-1"><h2 className="font-display text-xl text-coffee">{t}</h2><div className="mt-2 text-sm">{children}</div></div></section>
function How({queue,next,go}:{queue:Customer[];next?:Customer;go:()=>void}){
  const top=queue.slice(0,7)
  const P=[[250,32],[110,106],[390,106],[50,180],[170,180],[330,180],[450,180]]
  return<div className="space-y-4 max-w-3xl">
    <div><h1 className="font-display text-3xl text-coffee">How Prioritization Works</h1><p className="text-sm text-muted">One request, followed from input to the next decision.</p></div>
    <Step n={1} t="Dynamic Priority">{next?<div className="flex flex-wrap gap-x-6 gap-y-1"><b className="text-coffee">{next.customer_id}</b><span>Urgency: {String(next.urgency).toUpperCase()}</span><span>Wait: {f1(next.waiting_time)} min</span><span>Service: {next.service_type}</span></div>:<p className="text-muted">No next request is currently returned by the selected context.</p>}</Step>
    <Step n={2} t="Urgency + Waiting Time + Service Requirement"><p>The selected context supplies the accepted urgency and service values. The engine updates waiting time as requests age.</p></Step>
    <Step n={3} t="Priority Score"><div className="font-mono text-coffee text-base">P = 0.50·U + 0.30·W + 0.20·S</div><div className="grid grid-cols-3 gap-2 mt-3">{[['U','Urgency','50%','bg-terra'],['W','Waiting','30%','bg-caramel'],['S','Service','20%','bg-sage']].map(([a,b,w,c])=><div key={a} className="rounded-lg bg-cream/50 p-3"><b>{a}</b> {b} <span className="text-muted">{w}</span><div className="h-1.5 bg-cream rounded mt-2"><div className={`h-full rounded ${c}`} style={{width:w}}/></div></div>)}</div></Step>
    <Step n={4} t="Max Heap → Next Customer"><p>The backend heap keeps the highest-priority request at the root. That request is returned as next to serve.</p>
      {top.length>0?<svg viewBox="0 0 500 215" className="w-full max-w-lg mx-auto mt-2" role="img" aria-label="Priority heap, illustrative view">{top.map((_,i)=>i>0&&<line key={i} x1={P[(i-1)>>1][0]} y1={P[(i-1)>>1][1]+14} x2={P[i][0]} y2={P[i][1]-14} stroke="#B8794B" opacity=".5"/>)}
        {top.map((c,i)=><g key={c.customer_id} style={{transform:`translate(${P[i][0]}px,${P[i][1]}px)`,transition:'transform .5s ease'}}><rect x="-38" y="-22" width="76" height="44" rx="8" fill={i===0?'#B8794B':'#E9DCCB'}/><text textAnchor="middle" y="-3" fontSize="13" fontWeight="700" fill={i===0?'#fff':'#5A3E32'}>{c.customer_id}</text><text textAnchor="middle" y="13" fontSize="11" fill={i===0?'#fff':'#806F64'}>{f1(c.priority_score)}</text></g>)}</svg>:<p className="text-muted mt-2">Open the Live Queue to populate this view.</p>}
      <p className="text-xs text-muted mt-2"><b>Priority Heap — Illustrative View.</b> This draws the top of the backend’s priority-ordered queue in heap layout to show ordering. It is not the backend’s internal heap array.</p></Step>
    <Step n={5} t="Aging"><p>Every minute a request waits raises its waiting-time contribution, allowing a lower-urgency request to overtake newer requests when its total priority becomes higher.</p>
      <div className="flex items-end gap-1 h-12 mt-3" aria-hidden>{[1,2,3,4,5,6,7,8].map(i=><div key={i} className="flex-1 bg-caramel/70 rounded-t" style={{height:`${i*12}%`}}/>)}</div><div className="flex justify-between text-xs text-muted"><span>just arrived</span><span>waiting longer →</span></div><p className="text-xs text-muted">Conceptual sketch, not measured data.</p></Step>
    <Step n={6} t="Serve → Metrics"><p>Serving removes the selected customer. The backend then refreshes queue counts, waiting and service averages, and throughput for that context.</p></Step>
    <section className="card p-5 !border-caramel bg-caramel/5 flex flex-wrap items-center gap-3"><div className="flex-1"><div className="text-xs font-bold text-caramel tracking-widest">RESULT</div><div className="font-display text-2xl text-coffee">{next?`Next request → ${next.customer_id}`:'Waiting for the next request'}</div></div><Btn p onClick={go}>View it in the Live Queue</Btn></section>
    <section className="card p-5"><h2 className="font-semibold text-coffee mb-2 text-sm">Complexity (binary heap)</h2><div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-sm">{[['Insert','O(log n)'],['Extract max','O(log n)'],['Peek','O(1)'],['Full dynamic refresh','O(n)'],['Space','O(n)']].map(([a,b])=><div key={a} className="rounded bg-cream/50 p-2"><div className="text-xs text-muted">{a}</div><b className="font-mono">{b}</b></div>)}</div><p className="text-xs text-muted mt-2">Refreshing waiting-time scores touches every waiting request, so a full refresh is O(n), not O(log n).</p></section></div>
}

function Perf({hist,m,comparison,comparisonError,loaded,failure,retry,context}:{hist:{t:string;len:number;avg:number}[];m:Metrics|null;comparison:ComparisonResponse|null;comparisonError:string|null;loaded:boolean;failure:RequestFailure|null;retry:()=>void;context:Ctx}){
  const S3:[string,string,string][]=[['FCFS','FCFS','#806F64'],['Static Priority','STATIC_PRIORITY','#B8794B'],['Dynamic Priority','DYNAMIC_PRIORITY_QUEUE','#B85C4A']]
  const stats=(algorithm:string)=>comparison?.results.find(result=>result.algorithm===algorithm)
  const data=[['Avg waiting','average_waiting_time'],['Max waiting','maximum_waiting_time'],['Avg turnaround','average_turnaround_time']].map(([n,k])=>({n,...Object.fromEntries(S3.map(([label,algorithm])=>[label,(stats(algorithm) as any)?.[k]]))}))
  const ax={stroke:'#806F64',fontSize:11}
  if(failure)return<div className="card p-8 text-center" role="alert"><h2 className="font-display text-2xl text-terra">{failure.kind==='unavailable'?'Queue engine unavailable':'Queue API error'}</h2><p className="text-muted">{failure.message}</p><Btn p className="mt-3" onClick={retry}>Retry Connection</Btn></div>
  if(!loaded)return<div className="space-y-3"><div className="skel h-24"/><div className="skel h-64"/></div>
  const line=(t:string,k:'len'|'avg',u:string,col:string)=><div className="card p-4"><h3 className="text-sm font-semibold text-coffee">{t}</h3>{hist.length<2?<p className="text-sm text-muted py-12 text-center">Collecting samples… (one every 5 s)</p>:<div className="h-52 mt-2"><ResponsiveContainer><LineChart data={hist}><CartesianGrid stroke="#E4D5C6" strokeDasharray="3 3"/><XAxis dataKey="t" {...ax} minTickGap={40}><Label value="Sample time" offset={-2} position="insideBottom" fontSize={11} fill="#806F64"/></XAxis><YAxis {...ax} allowDecimals={false}><Label value={u} angle={-90} position="insideLeft" fontSize={11} fill="#806F64"/></YAxis><Tooltip/><Legend verticalAlign="top"/><Line name={t} dataKey={k} stroke={col} strokeWidth={2} dot={false}/></LineChart></ResponsiveContainer></div>}</div>
  return<div className="space-y-5"><div><h1 className="font-display text-3xl text-coffee">Performance</h1><p className="text-sm text-muted">Does dynamic prioritization change queue behavior? Comparing the current {context.label} waiting queue.</p></div>
    <section className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-line border border-line rounded-xl overflow-hidden">{[['Average waiting',`${f1(m?.average_waiting_time)} min`],['Maximum waiting',`${f1(m?.maximum_waiting_time)} min`],['Throughput',`${m?.throughput??'—'} / hr`],['Queue length',`${m?.queue_length??'—'}`]].map(([k,v])=><div key={k} className="bg-surface px-4 py-3"><div className="text-xs text-muted">{k}</div><div className="num font-bold text-lg text-coffee">{v}</div></div>)}</section>
    <section className="card p-5"><h2 className="font-display text-xl text-coffee">FCFS vs Static Priority vs Dynamic Priority</h2><p className="text-xs text-muted mb-3">Same current-context dataset for all three. Lower is better.</p>
      {comparisonError?<p role="alert" className="text-sm text-terra py-4">Comparison unavailable: {comparisonError}</p>:!comparison?<p className="text-sm text-muted py-10 text-center">No comparison data returned by the backend yet.</p>:<><div className="h-64"><ResponsiveContainer><BarChart data={data}><CartesianGrid stroke="#E4D5C6" strokeDasharray="3 3"/><XAxis dataKey="n" {...ax}/><YAxis {...ax}><Label value="Minutes" angle={-90} position="insideLeft" fontSize={11} fill="#806F64"/></YAxis><Tooltip/><Legend/>{S3.map(([label,,color])=><Bar key={label} dataKey={label} fill={color} radius={[3,3,0,0]}/>)}</BarChart></ResponsiveContainer></div>
        <div className="overflow-x-auto mt-3"><table className="w-full text-sm min-w-[420px]"><thead><tr className="text-left text-xs text-muted"><th className="py-1">Strategy</th><th>Avg wait</th><th>Max wait</th><th>Avg turnaround</th></tr></thead><tbody>{S3.map(([label,algorithm])=>{const result=stats(algorithm);const dynamic=algorithm==='DYNAMIC_PRIORITY_QUEUE';return<tr key={algorithm} className={`border-t border-line ${dynamic?'bg-caramel/5':''}`}><td className={`py-2 font-semibold ${dynamic?'text-terra':'text-coffee'}`}>{label}{dynamic&&<> <span className="ml-2 text-[10px] font-medium uppercase tracking-wide text-muted">Queue policy</span></>}</td><td className="num">{f1(result?.average_waiting_time)} min</td><td className="num">{f1(result?.maximum_waiting_time)} min</td><td className="num">{f1(result?.average_turnaround_time)} min</td></tr>})}</tbody></table></div></>}</section>
    <div className="grid md:grid-cols-2 gap-5">{line('Queue length','len','Requests','#5A3E32')}{line('Average waiting time','avg','Minutes','#B8794B')}</div></div>
}
