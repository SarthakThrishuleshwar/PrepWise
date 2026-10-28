/**
 * Feature E: Plan comparison and export screen (ChangesPage).
 *
 * Implements:
 * 1. "What changed": Factual before/after differences vs parent plan (or baseline v1),
 *    change counts (added, moved, resized, deferred, removed, unchanged),
 *    dual move+resize support, and "Reason unavailable" for unverified removals.
 * 2. "Why": Saved reason codes and verified supporting references without causal prose.
 * 3. "What to do next": Practical navigation actions grounded in the returned factual state.
 * 4. Factual feasibility words + numbers (full/partial/no_capacity, minutes, shortfall, conflicts).
 * 5. Plan export & exact in-app preview: single-fetch of CSV/JSON, Blob retention,
 *    live text preview, and download from the exact same Blob with race prevention and cancellation.
 */

import { useEffect, useRef, useState, useTransition } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  ArrowDown,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  FileCode,
  FileSpreadsheet,
  FileText,
  Info,
  RefreshCw,
  Sliders,
} from 'lucide-react'
import { api, ApiError } from '../../lib/api'
import { ActionLink, Button, Eyebrow, Notice, Panel } from '../../components/ui'

export interface PlacementInfo {
  date: string
  sequence: number
  duration_minutes: number
}

export interface ChangeItem {
  work_item_id: string
  topic_id: string
  activity_kind: string
  is_added: boolean
  is_moved: boolean
  is_resized: boolean
  is_deferred: boolean
  is_removed: boolean
  previous_placement: PlacementInfo | null
  new_placement: PlacementInfo | null
  previous_duration_minutes: number | null
  new_duration_minutes: number | null
  reason_code: string | null
  evidence: Record<string, unknown>
}

export interface PlanMetrics {
  capacity_minutes: number
  remaining_work_minutes: number
  scheduled_minutes: number
  deferred_minutes: number
  minute_shortfall: number
  placement_conflict_count: number
}

export interface PlanChangesResponse {
  plan_id: string
  goal_id: string
  version: number
  parent_plan_id: string | null
  is_baseline: boolean
  feasibility: 'full' | 'partial' | 'no_capacity'
  counts: {
    added: number
    moved: number
    resized: number
    deferred: number
    removed: number
    unchanged: number
  }
  unchanged_count: number
  metrics: PlanMetrics
  changes: ChangeItem[]
}

export function ChangesPage() {
  const [searchParams] = useSearchParams()
  const paramPlanId = searchParams.get('plan_id')?.trim() || null

  const [resolvedPlanId, setResolvedPlanId] = useState<string | null>(paramPlanId)
  const [data, setData] = useState<PlanChangesResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<{ message: string; code?: string } | null>(null)
  const [reloadKey, setReloadKey] = useState<number>(0)

  // Export & Preview state
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('json')
  const [previewBlob, setPreviewBlob] = useState<Blob | null>(null)
  const [previewText, setPreviewText] = useState<string | null>(null)
  const [previewFilename, setPreviewFilename] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState<boolean>(false)
  const [previewError, setPreviewError] = useState<string | null>(null)

  // Token ref to eliminate async race conditions on export preview
  const previewRequestIdRef = useRef<number>(0)
  const previewAbortControllerRef = useRef<AbortController | null>(null)

  const [, startTransition] = useTransition()

  // 1. Resolve Plan ID if not in query param
  useEffect(() => {
    if (paramPlanId) {
      setResolvedPlanId(paramPlanId)
      return
    }

    const savedGoalId = localStorage.getItem('learnnova.goal-id')
    if (!savedGoalId) {
      setLoading(false)
      setResolvedPlanId(null)
      return
    }

    let active = true
    api<{ plan_id: string }>(`/goals/${savedGoalId}/plans/current`)
      .then((res) => {
        if (active && res.plan_id) {
          setResolvedPlanId(res.plan_id)
        } else if (active) {
          setResolvedPlanId(null)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (active) {
          setResolvedPlanId(null)
          setLoading(false)
          // Distinguish actual 404 (no plan generated yet) from real network/auth errors
          if (err instanceof ApiError) {
            if (err.code !== 'PLAN_NOT_FOUND') {
              setError({ message: err.message, code: err.code })
            }
          } else {
            setError({ message: 'Unable to reach the server to determine the current plan.' })
          }
        }
      })

    return () => {
      active = false
    }
  }, [paramPlanId])

  // 2. Fetch Comparison Data
  useEffect(() => {
    // Clear old data immediately on plan change so an error cannot leave stale data visible
    setData(null)
    setPreviewText(null)
    setPreviewBlob(null)
    setPreviewError(null)

    if (!resolvedPlanId) {
      setLoading(false)
      return
    }

    let active = true
    setLoading(true)
    setError(null)

    api<PlanChangesResponse>(`/plans/${resolvedPlanId}/changes`)
      .then((res) => {
        if (active) {
          setData(res)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (active) {
          setData(null)
          setLoading(false)
          if (err instanceof ApiError) {
            setError({ message: err.message, code: err.code })
          } else {
            setError({ message: 'Unable to reach the server to load plan comparison.' })
          }
        }
      })

    return () => {
      active = false
    }
  }, [resolvedPlanId, reloadKey])

  // 3. Clear preview immediately on format or plan change and abort active request
  useEffect(() => {
    if (previewAbortControllerRef.current) {
      previewAbortControllerRef.current.abort()
      previewAbortControllerRef.current = null
    }
    setPreviewText(null)
    setPreviewBlob(null)
    setPreviewFilename('')
    setPreviewError(null)
    setPreviewLoading(false)
  }, [exportFormat, resolvedPlanId])

  // 4. Feature-local single-fetch for plan export & exact preview with AbortController and generation token
  const handleFetchPreview = async () => {
    if (!resolvedPlanId) return

    // Cancel any in-flight preview request
    if (previewAbortControllerRef.current) {
      previewAbortControllerRef.current.abort()
    }
    const abortController = new AbortController()
    previewAbortControllerRef.current = abortController

    // Increment request token
    const currentToken = ++previewRequestIdRef.current
    const currentRequestedPlan = resolvedPlanId
    const currentRequestedFormat = exportFormat

    // Clear old blob, text, and filename immediately on new preview fetch
    setPreviewBlob(null)
    setPreviewText(null)
    setPreviewFilename('')
    setPreviewError(null)
    setPreviewLoading(true)

    try {
      const headers = new Headers()
      const token = localStorage.getItem('learnnova.token')
      if (token) headers.set('X-Local-Token', token)

      const res = await fetch(`/api/v1/plans/${resolvedPlanId}/export?format=${exportFormat}`, {
        headers,
        signal: abortController.signal,
      })

      if (!res.ok) {
        let errMessage = 'Failed to fetch export.'
        try {
          const jsonErr = await res.json()
          if (jsonErr.error?.message) errMessage = jsonErr.error.message
        } catch {
          // fallback text
        }
        throw new Error(errMessage)
      }

      // Check request token to ensure late response cannot overwrite newer selection
      if (
        currentToken !== previewRequestIdRef.current ||
        resolvedPlanId !== currentRequestedPlan ||
        exportFormat !== currentRequestedFormat
      ) {
        return
      }

      let filename = `plan-${resolvedPlanId}-v${data?.version || 1}.${exportFormat}`
      const disposition = res.headers.get('Content-Disposition')
      if (disposition && disposition.includes('filename=')) {
        const match = disposition.match(/filename="?([^"]+)"?/)
        if (match && match[1]) {
          filename = match[1]
        }
      }

      const blob = await res.blob()
      const text = await blob.text()

      if (currentToken !== previewRequestIdRef.current) {
        return
      }

      startTransition(() => {
        setPreviewBlob(blob)
        setPreviewText(text)
        setPreviewFilename(filename)
        setPreviewLoading(false)
      })
    } catch (err: unknown) {
      if (abortController.signal.aborted) {
        return
      }
      if (currentToken === previewRequestIdRef.current) {
        const msg = err instanceof Error ? err.message : 'Error retrieving export.'
        setPreviewError(msg)
        setPreviewLoading(false)
      }
    }
  }

  // 5. Download the exact same blob as previewed
  const handleDownloadBlob = () => {
    if (!previewBlob) return
    const url = URL.createObjectURL(previewBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = previewFilename || `plan-export.${exportFormat}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Render: No plan selected / honest empty state
  if (!resolvedPlanId && !loading) {
    return (
      <section className="container page-section" aria-labelledby="changes-title">
        <Eyebrow>Plan comparison</Eyebrow>
        <h1 id="changes-title" className="page-title">
          Compare plan versions.
          <br />
          See every factual reason.
        </h1>
        <p className="page-intro">
          Review what changed between your schedules and export your exact plan.
        </p>
        <Panel className="panel--quiet" style={{ padding: '32px', textAlign: 'center' }}>
          <Info size={36} aria-hidden="true" style={{ margin: '0 auto 16px', color: 'var(--dp-color-accent)' }} />
          <h2 style={{ fontSize: '18px', marginBottom: '8px' }}>No plan version selected</h2>
          <p style={{ color: 'var(--dp-color-ink-secondary)', maxWidth: '540px', margin: '0 auto 24px' }}>
            To view comparisons, open a plan directly from your workspace or create your first learning schedule.
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <ActionLink to="/plan">View current plan</ActionLink>
            <ActionLink to="/setup" secondary>Set up a goal</ActionLink>
          </div>
        </Panel>
      </section>
    )
  }

  return (
    <section className="container page-section" aria-labelledby="changes-title">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <Eyebrow>Plan comparison & export</Eyebrow>
          <h1 id="changes-title" className="page-title">
            Factual plan transitions.
            <br />
            Before, after, and why.
          </h1>
          <p className="page-intro">
            Every change reflects genuine schedule placement, duration, and verified evidence.
          </p>
        </div>
        {data && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span className="tag" style={{ background: 'var(--dp-color-ground-muted)', padding: '6px 12px', borderRadius: '6px', fontSize: '13px' }}>
              Selected: Version {data.version}
            </span>
            {data.parent_plan_id ? (
              <span className="tag" style={{ background: 'var(--dp-color-ground-muted)', padding: '6px 12px', borderRadius: '6px', fontSize: '13px' }}>
                Compared with Parent
              </span>
            ) : (
              <span className="tag" style={{ background: 'var(--dp-color-ground-muted)', padding: '6px 12px', borderRadius: '6px', fontSize: '13px' }}>
                Initial baseline (v1)
              </span>
            )}
          </div>
        )}
      </div>

      {/* Loading & Error States */}
      {loading && <Notice>Loading plan comparison…</Notice>}
      {error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <Notice error>{error.message}</Notice>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="secondary" onClick={() => setReloadKey((k) => k + 1)}>
              <RefreshCw size={14} style={{ marginRight: '6px' }} /> Try again
            </Button>
            <ActionLink to="/plan" secondary>Return to plan</ActionLink>
          </div>
        </div>
      )}

      {data && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {/* Feasibility Overview Banner: Words + Saved Numeric Metrics */}
          <Panel style={{ padding: '24px', borderLeft: '4px solid var(--dp-color-accent)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Sliders size={20} color="var(--dp-color-accent)" aria-hidden="true" />
                <h2 style={{ fontSize: '18px', margin: 0 }}>
                  Feasibility: <strong style={{ textTransform: 'capitalize' }}>{data.feasibility.replace('_', ' ')}</strong>
                </h2>
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                gap: '16px',
                paddingTop: '16px',
                borderTop: '1px solid var(--dp-color-rule)',
              }}
            >
              <div>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--dp-color-ink-secondary)' }}>Capacity</p>
                <p style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 600 }}>{data.metrics.capacity_minutes}m</p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--dp-color-ink-secondary)' }}>Scheduled</p>
                <p style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 600 }}>{data.metrics.scheduled_minutes}m</p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--dp-color-ink-secondary)' }}>Deferred</p>
                <p style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 600 }}>{data.metrics.deferred_minutes}m</p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--dp-color-ink-secondary)' }}>Shortfall</p>
                <p style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 600, color: data.metrics.minute_shortfall > 0 ? '#b91c1c' : 'inherit' }}>
                  {data.metrics.minute_shortfall}m
                </p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--dp-color-ink-secondary)' }}>Placement Conflicts</p>
                <p style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 600 }}>{data.metrics.placement_conflict_count}</p>
              </div>
            </div>
          </Panel>

          {/* SECTION 1: "What changed" */}
          <section aria-labelledby="section-what-changed">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
              <div>
                <h2 id="section-what-changed" style={{ fontSize: '20px', margin: 0 }}>
                  1. What changed
                </h2>
                <p style={{ margin: '4px 0 0', color: 'var(--dp-color-ink-secondary)', fontSize: '14px' }}>
                  {data.is_baseline
                    ? 'Initial version (v1): Baseline schedule with no parent plan differences.'
                    : `Comparing version ${data.version} against its parent schedule.`}
                </p>
              </div>

              {/* Summary Metric Chips */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }} aria-label="Change summary counts">
                <span className="tag" style={{ background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  +{data.counts.added} added
                </span>
                <span className="tag" style={{ background: '#eff6ff', color: '#1e40af', border: '1px solid #bfdbfe', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  {data.counts.moved} moved
                </span>
                <span className="tag" style={{ background: '#fefce8', color: '#854d0e', border: '1px solid #fef08a', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  {data.counts.resized} resized
                </span>
                <span className="tag" style={{ background: '#fff7ed', color: '#9a3412', border: '1px solid #fed7aa', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  {data.counts.deferred} deferred
                </span>
                <span className="tag" style={{ background: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  {data.counts.removed} removed
                </span>
                <span className="tag" style={{ background: 'var(--dp-color-ground-muted)', color: 'var(--dp-color-ink-secondary)', border: '1px solid var(--dp-color-rule)', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  {data.unchanged_count} unchanged between versions
                </span>
              </div>
            </div>

            {data.is_baseline ? (
              <Panel style={{ padding: '24px', textAlign: 'center' }}>
                <CheckCircle2 size={32} color="var(--dp-color-accent)" aria-hidden="true" style={{ margin: '0 auto 12px' }} />
                <h3 style={{ fontSize: '16px', marginBottom: '8px' }}>Initial Schedule Baseline</h3>
                <p style={{ color: 'var(--dp-color-ink-secondary)', maxWidth: '520px', margin: '0 auto' }}>
                  This is the first generated version of your plan. All scheduled items represent starting baseline work. Future replans will compare against this version.
                </p>
              </Panel>
            ) : data.changes.length === 0 ? (
              <Panel style={{ padding: '24px', textAlign: 'center' }}>
                <p style={{ color: 'var(--dp-color-ink-secondary)', margin: 0 }}>
                  No changes recorded. All {data.unchanged_count} work items remain in identical placement and duration between versions.
                </p>
              </Panel>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {data.changes.map((item) => (
                  <Panel key={item.work_item_id} style={{ padding: '16px 20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                      {/* Topic & Kind Identity */}
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <strong style={{ fontSize: '15px' }}>{item.topic_id || 'Unknown topic'}</strong>
                          <span style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--dp-color-ink-secondary)', letterSpacing: '0.05em' }}>
                            ({item.activity_kind})
                          </span>

                          {/* Distinct tags for Move and Resize */}
                          {item.is_added && <span className="tag" style={{ background: '#dcfce7', color: '#15803d', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>Added</span>}
                          {item.is_moved && <span className="tag" style={{ background: '#dbeafe', color: '#1d4ed8', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>Moved</span>}
                          {item.is_resized && <span className="tag" style={{ background: '#fef9c3', color: '#a16207', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>Resized</span>}
                          {item.is_deferred && <span className="tag" style={{ background: '#ffedd5', color: '#c2410c', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>Deferred</span>}
                          {item.is_removed && <span className="tag" style={{ background: '#fee2e2', color: '#b91c1c', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>Removed</span>}
                        </div>
                        <p style={{ margin: 0, fontSize: '12px', color: 'var(--dp-color-ink-secondary)', fontFamily: 'monospace' }}>
                          ID: {item.work_item_id}
                        </p>
                      </div>

                      {/* Before / After Transitions */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '13px' }}>
                        {/* Before */}
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '11px', color: 'var(--dp-color-ink-secondary)', display: 'block' }}>Before</span>
                          {item.previous_placement ? (
                            <span>
                              <Calendar size={12} style={{ display: 'inline', marginRight: '4px' }} />
                              {item.previous_placement.date} (#{item.previous_placement.sequence}) · {item.previous_duration_minutes}m
                            </span>
                          ) : (
                            <span style={{ color: 'var(--dp-color-ink-secondary)' }}>None</span>
                          )}
                        </div>

                        <ArrowRight size={16} color="var(--dp-color-ink-secondary)" aria-hidden="true" />

                        {/* After */}
                        <div>
                          <span style={{ fontSize: '11px', color: 'var(--dp-color-ink-secondary)', display: 'block' }}>After</span>
                          {item.new_placement ? (
                            <span style={{ fontWeight: 500 }}>
                              <Calendar size={12} style={{ display: 'inline', marginRight: '4px' }} />
                              {item.new_placement.date} (#{item.new_placement.sequence}) · {item.new_duration_minutes}m
                            </span>
                          ) : item.is_deferred ? (
                            <span style={{ color: '#c2410c', fontWeight: 500 }}>
                              Deferred ({item.new_duration_minutes || item.previous_duration_minutes}m)
                            </span>
                          ) : item.is_removed ? (
                            <span style={{ color: '#b91c1c', fontWeight: 500 }}>Removed from plan</span>
                          ) : (
                            <span style={{ color: 'var(--dp-color-ink-secondary)' }}>None</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* SECTION 2: "Why" (Factual reason and references) */}
                    <div
                      style={{
                        marginTop: '12px',
                        paddingTop: '10px',
                        borderTop: '1px solid var(--dp-color-rule)',
                        fontSize: '13px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '8px',
                      }}
                    >
                      <div>
                        <span style={{ color: 'var(--dp-color-ink-secondary)', marginRight: '6px' }}>Reason:</span>
                        {item.reason_code ? (
                          <code style={{ background: 'var(--dp-color-ground-muted)', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>
                            {item.reason_code}
                          </code>
                        ) : item.is_removed ? (
                          <span style={{ color: 'var(--dp-color-ink-secondary)', fontStyle: 'italic' }}>Reason unavailable</span>
                        ) : (
                          <span style={{ color: 'var(--dp-color-ink-secondary)' }}>No reason code recorded</span>
                        )}
                      </div>

                      <div>
                        {item.evidence && Object.keys(item.evidence).length > 0 ? (
                          <span style={{ fontSize: '12px', color: 'var(--dp-color-ink-secondary)' }}>
                            Evidence:{' '}
                            {Object.entries(item.evidence).map(([k, v]) => (
                              <code key={k} style={{ marginLeft: '4px', background: 'var(--dp-color-ground-muted)', padding: '1px 5px', borderRadius: '3px' }}>
                                {k}={String(v)}
                              </code>
                            ))}
                          </span>
                        ) : (
                          <span style={{ fontSize: '12px', color: 'var(--dp-color-ink-secondary)' }}>
                            No supporting event reference is available.
                          </span>
                        )}
                      </div>
                    </div>
                  </Panel>
                ))}
              </div>
            )}
          </section>

          {/* SECTION 3: "What to do next" (Actionable navigation grounded in factual state) */}
          <section aria-labelledby="section-next-steps">
            <h2 id="section-next-steps" style={{ fontSize: '20px', marginBottom: '8px' }}>
              3. What to do next
            </h2>
            <p style={{ margin: '0 0 16px', color: 'var(--dp-color-ink-secondary)', fontSize: '14px' }}>
              Grounded navigation based on plan state ({data.unchanged_count} tasks unchanged between versions):
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
              <Panel style={{ padding: '20px' }}>
                <Clock size={20} color="var(--dp-color-accent)" aria-hidden="true" style={{ marginBottom: '8px' }} />
                <h3 style={{ fontSize: '16px', margin: '0 0 6px' }}>View scheduled plan</h3>
                <p style={{ fontSize: '13px', color: 'var(--dp-color-ink-secondary)', margin: '0 0 12px' }}>
                  Open your current timetable to view scheduled session times and activities.
                </p>
                <ActionLink to="/plan">Open my plan</ActionLink>
              </Panel>

              {data.counts.deferred > 0 || data.metrics.minute_shortfall > 0 ? (
                <Panel style={{ padding: '20px' }}>
                  <Sliders size={20} color="#c2410c" aria-hidden="true" style={{ marginBottom: '8px' }} />
                  <h3 style={{ fontSize: '16px', margin: '0 0 6px' }}>Adjust availability</h3>
                  <p style={{ fontSize: '13px', color: 'var(--dp-color-ink-secondary)', margin: '0 0 12px' }}>
                    {data.counts.deferred} task(s) are recorded as deferred ({data.metrics.deferred_minutes}m). You can adjust dated study minutes in setup.
                  </p>
                  <ActionLink to="/setup" secondary>Edit availability</ActionLink>
                </Panel>
              ) : (
                <Panel style={{ padding: '20px' }}>
                  <CheckCircle2 size={20} color="#15803d" aria-hidden="true" style={{ marginBottom: '8px' }} />
                  <h3 style={{ fontSize: '16px', margin: '0 0 6px' }}>Open activities</h3>
                  <p style={{ fontSize: '13px', color: 'var(--dp-color-ink-secondary)', margin: '0 0 12px' }}>
                    View learning activities for your active schedule.
                  </p>
                  <ActionLink to="/study" secondary>Go to activities</ActionLink>
                </Panel>
              )}

              <Panel style={{ padding: '20px' }}>
                <FileText size={20} color="var(--dp-color-accent)" aria-hidden="true" style={{ marginBottom: '8px' }} />
                <h3 style={{ fontSize: '16px', margin: '0 0 6px' }}>Export this plan</h3>
                <p style={{ fontSize: '13px', color: 'var(--dp-color-ink-secondary)', margin: '0 0 12px' }}>
                  Preview and download this exact version as CSV or JSON below.
                </p>
                <a href="#export-section" className="button button--secondary" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  Jump to export <ArrowDown size={14} />
                </a>
              </Panel>
            </div>
          </section>

          {/* Plan Export & Exact Preview Section */}
          <section id="export-section" aria-labelledby="section-export" style={{ paddingTop: '16px', borderTop: '1px solid var(--dp-color-rule)' }}>
            <h2 id="section-export" style={{ fontSize: '20px', marginBottom: '8px' }}>
              Plan export & in-app preview
            </h2>
            <p style={{ margin: '0 0 16px', color: 'var(--dp-color-ink-secondary)', fontSize: '14px' }}>
              Inspect the exact file contents before downloading. The file you download is saved directly from this single preview fetch.
            </p>

            <Panel style={{ padding: '24px' }}>
              {/* Format selection and preview action */}
              <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
                <fieldset style={{ border: 'none', padding: 0, margin: 0, display: 'flex', gap: '12px' }}>
                  <legend className="sr-only">Choose export format</legend>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      padding: '8px 14px',
                      borderRadius: '6px',
                      border: exportFormat === 'json' ? '2px solid var(--dp-color-accent)' : '1px solid var(--dp-color-rule)',
                      background: exportFormat === 'json' ? '#eff6ff' : 'transparent',
                    }}
                  >
                    <input
                      type="radio"
                      name="exportFormat"
                      value="json"
                      checked={exportFormat === 'json'}
                      onChange={() => setExportFormat('json')}
                    />
                    <FileCode size={16} aria-hidden="true" /> JSON Document
                  </label>

                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      padding: '8px 14px',
                      borderRadius: '6px',
                      border: exportFormat === 'csv' ? '2px solid var(--dp-color-accent)' : '1px solid var(--dp-color-rule)',
                      background: exportFormat === 'csv' ? '#eff6ff' : 'transparent',
                    }}
                  >
                    <input
                      type="radio"
                      name="exportFormat"
                      value="csv"
                      checked={exportFormat === 'csv'}
                      onChange={() => setExportFormat('csv')}
                    />
                    <FileSpreadsheet size={16} aria-hidden="true" /> CSV Spreadsheet
                  </label>
                </fieldset>

                <Button variant="secondary" onClick={handleFetchPreview} disabled={previewLoading}>
                  <Eye size={15} style={{ marginRight: '6px' }} />
                  {previewLoading ? 'Loading preview…' : 'Preview export'}
                </Button>

                {previewBlob && (
                  <Button variant="primary" onClick={handleDownloadBlob}>
                    <Download size={15} style={{ marginRight: '6px' }} />
                    Download {previewFilename || `plan-v${data.version}.${exportFormat}`}
                  </Button>
                )}
              </div>

              {previewError && <Notice error>{previewError}</Notice>}

              {/* Exact In-App Preview Window */}
              {previewText !== null && (
                <div style={{ marginTop: '16px' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      background: 'var(--dp-color-field)',
                      color: 'var(--dp-color-on-field)',
                      padding: '8px 16px',
                      borderTopLeftRadius: '8px',
                      borderTopRightRadius: '8px',
                      fontSize: '12px',
                    }}
                  >
                    <span>Previewing exact payload: {previewFilename}</span>
                    <span style={{ color: 'var(--dp-color-on-field-secondary)' }}>
                      {(previewBlob?.size || 0) > 1024
                        ? `${((previewBlob?.size || 0) / 1024).toFixed(1)} KB`
                        : `${previewBlob?.size || 0} bytes`}
                    </span>
                  </div>
                  <pre
                    tabIndex={0}
                    aria-label={`Exact export preview for ${previewFilename}`}
                    style={{
                      margin: 0,
                      padding: '16px',
                      background: '#0d1117',
                      color: '#c9d1d9',
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      lineHeight: '1.5',
                      maxHeight: '380px',
                      overflow: 'auto',
                      borderBottomLeftRadius: '8px',
                      borderBottomRightRadius: '8px',
                      whiteSpace: exportFormat === 'csv' ? 'pre' : 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {previewText}
                  </pre>
                </div>
              )}
            </Panel>
          </section>
        </div>
      )}
    </section>
  )
}
