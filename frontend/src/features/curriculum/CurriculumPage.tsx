import { useEffect,useState } from 'react'
import { BookOpen,ArrowRight } from 'lucide-react'
import { api } from '../../lib/api'
import type { Curriculum } from '../../lib/api'
import { ActionLink,Button,Eyebrow,Notice,Panel } from '../../components/ui'

export function CurriculumPage(){
 const [data,setData]=useState<Curriculum|null>(null),[error,setError]=useState(''),[reload,setReload]=useState(0)
 useEffect(()=>{let active=true;setError('');api<{id:string}[]>('/curricula').then(async rows=>{if(!rows.length)throw new Error('No curriculum is seeded yet.');const value=await api<Curriculum>(`/curricula/${rows[0].id}`);if(active)setData(value)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[reload])
 return <section className="container page-section"><Eyebrow>Your curriculum</Eyebrow><h1 className="page-title">Start with the foundations.<br/>See how they connect.</h1><p className="page-intro">A structured reference curriculum gives your plan a clear starting point.</p>{error?<><Notice error>{error}</Notice><Button variant="secondary" onClick={()=>setReload(reload+1)}>Try again</Button></>:!data?<Notice>Loading the curriculum…</Notice>:<><div className="curriculum-heading"><span className="tag"><BookOpen size={15} aria-hidden="true"/>{data.title} · v{data.version}</span><ActionLink to="/setup">Choose your topics</ActionLink></div><div className="curriculum-grid">{data.topics.map((topic,index)=>{const parents=data.prerequisites.filter(edge=>edge.topic_id===topic.id).map(edge=>String(data.topics.find(t=>t.id===edge.prerequisite_topic_id)?.title??edge.prerequisite_topic_id));return <Panel key={String(topic.id)} className="topic-panel"><span className="topic-number">{String(index+1).padStart(2,'0')}</span><h2>{String(topic.title)}</h2><p>{String(topic.objective)}</p><div className="topic-prerequisite"><ArrowRight size={14} aria-hidden="true"/>{parents.length?`After ${parents.join(' + ')}`:'A starting foundation'}</div></Panel>})}</div><p className="field-help">Assessment items remain draft until reviewed. Curriculum resources and semantic retrieval are owned by Member 2.</p></>}</section>
}
