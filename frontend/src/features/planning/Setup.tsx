import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowRight, Check, CalendarDays } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, ensureProfile, saveGoal } from '../../lib/api'
import type { Curriculum, SavedGoal } from '../../lib/api'
import { Button, Eyebrow, Notice, Panel } from '../../components/ui'

function localDate(value: Date) { return `${value.getFullYear()}-${String(value.getMonth()+1).padStart(2,'0')}-${String(value.getDate()).padStart(2,'0')}` }
function dateRows(start: string, end: string, minutes: number) {
  const rows: {date: string; minutes: number}[] = []
  const cursor = new Date(`${start}T12:00:00`), last = new Date(`${end}T12:00:00`)
  while (cursor <= last && rows.length < 31) { rows.push({date: localDate(cursor), minutes}); cursor.setDate(cursor.getDate()+1) }
  return rows
}

export function Setup() {
  const today = localDate(new Date())
  const later = new Date(); later.setDate(later.getDate()+6)
  const [name,setName] = useState(''), [title,setTitle] = useState('My next learning goal')
  const [start,setStart] = useState(today), [end,setEnd] = useState(localDate(later))
  const [minutes,setMinutes] = useState(60), [goalText,setGoalText] = useState('')
  const [curriculum,setCurriculum] = useState<Curriculum | null>(null), [targets,setTargets] = useState<string[]>([])
  const [error,setError] = useState(''), [loading,setLoading] = useState(true), [saving,setSaving] = useState(false), [saved,setSaved] = useState<SavedGoal | null>(null)
  const [reload,setReload] = useState(0)
  useEffect(()=>{let active=true; setLoading(true); setError(''); api<{id:string}[]>('/curricula').then(async rows=>{if (!rows.length) throw new Error('No curriculum is available yet. Run the curriculum seed command.'); const data=await api<Curriculum>(`/curricula/${rows[0].id}`); if(active) setCurriculum(data)}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)}); return()=>{active=false}},[reload])
  const rows=dateRows(start,end,minutes)
  async function submit(event:FormEvent) {
    event.preventDefault(); setError(''); setSaved(null)
    if(!curriculum || !targets.length) { setError('Choose at least one target topic.'); return }
    if(rows.length<1 || rows.length>30) { setError('Choose a study period between 1 and 30 days.'); return }
    setSaving(true)
    try { const profile=await ensureProfile(name); const result=await saveGoal({expected_revision:profile.input_revision,curriculum_id:curriculum.curriculum_id,title,goal_text:goalText,start_date:start,deadline:end,targets:targets.map(topic_id=>({topic_id,self_report:'unknown'})),availability:rows}); setSaved(result) }
    catch(e) { setError(e instanceof Error?e.message:'Please try again.') }
    finally { setSaving(false) }
  }
  return <section className="container page-section"><Eyebrow>Your workspace / Getting started</Eyebrow><h1 className="page-title">Let’s make space<br />for your learning.</h1><p className="page-intro">A few essentials to give your next step a clear direction. You can start without uploading a file.</p>
    <div className="setup-grid"><form onSubmit={submit} className="setup-form" aria-busy={saving}>
      {error&&<Notice error>{error}</Notice>}
      {loading?<Notice>Loading your curriculum…</Notice>:!curriculum?<Button type="button" variant="secondary" onClick={()=>setReload(reload+1)}>Retry curriculum connection</Button>:<>
      <fieldset><legend><span>01</span> A little about you</legend><div className="form-pair"><label>Your name <span className="optional">(optional)</span><input value={name} onChange={e=>setName(e.target.value)} maxLength={80} placeholder="What should we call you?" autoComplete="given-name" /></label><label>Goal title<input required value={title} onChange={e=>setTitle(e.target.value)} maxLength={120}/></label></div><label>What would you like to work toward? <span className="optional">(optional)</span><textarea value={goalText} onChange={e=>setGoalText(e.target.value)} maxLength={1000} placeholder="For example, feel confident tracing Python loops." rows={3}/></label><p className="field-help">This profile stays in your local workspace. Timezone: Asia/Kolkata.</p></fieldset>
      <fieldset><legend><span>02</span> Choose your direction</legend><p className="field-help" id="target-help">{curriculum.title} · Choose your target topics. The planner will include their foundations.</p><div className="topic-options" aria-describedby="target-help">{curriculum.topics.map(topic=><label className="check-option" key={String(topic.id)}><input type="checkbox" checked={targets.includes(String(topic.id))} onChange={e=>setTargets(e.target.checked?[...targets,String(topic.id)]:targets.filter(t=>t!==topic.id))}/><span>{String(topic.title)}</span></label>)}</div></fieldset>
      <fieldset><legend><span>03</span> Find your study window</legend><div className="form-pair"><label>Start date<input required type="date" value={start} min={today} onChange={e=>setStart(e.target.value)}/></label><label>Study deadline<input required type="date" value={end} min={start} onChange={e=>setEnd(e.target.value)}/></label></div><label>Available minutes each day<input required type="number" min={0} max={480} step={1} value={minutes} onChange={e=>setMinutes(Number(e.target.value))} aria-describedby="minutes-help"/></label><p className="field-help" id="minutes-help">This starting value applies to each date. Per-day editing belongs to the planning feature.</p></fieldset>
      <div className="form-actions"><Button type="submit" disabled={saving}>{saving?'Saving your workspace…':'Save my learning goal'}<ArrowRight size={17} aria-hidden="true"/></Button><span>No file upload needed</span></div>
      </>}
      {saved&&<Notice><strong><Check size={16} aria-hidden="true"/> Your goal is saved.</strong><p>{saved.title} is stored locally. Your planning feature can now use these inputs.</p><Link className="text-link" to="/plan">Open my plan <ArrowRight size={15} aria-hidden="true"/></Link></Notice>}
    </form><aside className="setup-aside"><Panel className="summary-panel"><span className="icon-tile"><CalendarDays size={24} aria-hidden="true"/></span><h2>A realistic starting point.</h2><p>Your available time is a planning constraint, not a promise of learning speed.</p><dl><div><dt>Study window</dt><dd>{rows.length>30?'Choose up to 30':rows.length} days</dd></div><div><dt>Daily availability</dt><dd>{minutes} min</dd></div><div><dt>Total allocated time</dt><dd>{rows.length>30?'—':rows.length*minutes} min</dd></div><div><dt>Target topics</dt><dd>{targets.length||'Not selected'}</dd></div></dl><p className="summary-note">Start with honest inputs. Build a useful plan from there.</p></Panel><p className="aside-note">Already have a local profile? Your saved identity is reused on this browser.</p></aside></div></section>
}
