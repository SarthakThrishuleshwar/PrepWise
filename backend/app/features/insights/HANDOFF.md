# Person 5 handoff — plan comparison and export

**Project:** LearnNova  
**Owner:** Person 5, Insights  
**Prepared:** 28 October 2026  
**Feature branch/commit:** `person-5` / `a6a1cdc`  
**Status:** Feature code is committed; integration and the open items below remain.

## What this gives the student

After a plan is updated, the student can review what was added, moved, resized, deferred or removed, alongside work that stayed unchanged. The Changes screen presents the old and new placement, the saved reason code, available supporting facts, feasibility totals and practical navigation actions. The student can preview and download a specific saved plan version as CSV or JSON.

Person 1 owns natural-language plan explanations. Insights presents saved facts and an explicit fallback when a reason or supporting event is unavailable. It does not schedule work, calculate learning scores or generate lessons.

## Implemented interfaces

| Interface | Purpose | Current state |
|---|---|---|
| `PlanDiffService.compare(parent, new_plan, work_item_contexts)` | Pure, deterministic comparison by stable work item ID | Implemented in [service.py](service.py) |
| `GET /api/v1/plans/{plan_id}/changes` | Authenticated comparison with the saved parent version | Implemented in [routes.py](routes.py) |
| `GET /api/v1/plans/{plan_id}/export?format=csv\|json` | Authenticated export of the requested saved plan version | Implemented in [routes.py](routes.py) and [export.py](export.py) |
| `ExportService.export_comparison(diff, format)` | CSV/JSON comparison-report serialization | Implemented internally; no student-facing route |
| `ChangesPage` | “What changed / Why / What to do next,” plan export preview and download | Exported by [ChangesPage.tsx](../../../../frontend/src/features/insights/ChangesPage.tsx); not mounted in `App.tsx` |

The changes API returns `is_baseline`, `feasibility`, metrics, counts (`added`, `moved`, `resized`, `deferred`, `removed`, `unchanged`) and a list of changed work items with before/after placement, flags, reason code and evidence fields. A moved and resized item retains both flags. The first version has no parent comparison. The API requires `X-Local-Token` and returns the same 404 for an unknown or unowned plan.

CSV distinguishes scheduled and deferred rows and neutralizes spreadsheet formula prefixes in text cells. The UI fetches a plan export once, displays its text, and downloads the same Blob. These services use read-only saved plan data; no other feature's scheduling or progress writes are changed.

## Integration requests

| Owner | Request |
|---|---|
| Person 1 | Mount `ChangesPage` at `/changes` in `frontend/src/App.tsx`; link to `/changes?plan_id=<saved plan ID>` from the Plan screen after a replan. Students should see version labels, not IDs. |
| Person 1 | Approve and publish the shared changes-response DTO, including the representation of a task that both moved and resized. The feature currently uses local response types. |
| Person 1 and Person 3 | Provide an authenticated list of saved versions for a goal if students should switch versions inside Changes. No version-list API or selector exists yet. |
| Person 1 | Approve a public route for comparison-report CSV/JSON downloads. The serializer exists, but the current public export endpoint exports only the selected plan. |
| Person 3 | Persist immutable plan versions with stable work item IDs, parent links, entries, deferred work, reason codes and input snapshots containing target scope when available. The insights adapter reads these records. |
| Person 4 | Provide saved progress events and evidence references. Insights currently verifies completion events; missed-event and assessment references are not yet linked as verified evidence. |

No change is requested from Person 2 for this feature.

## Person 5 items to finish before claiming a complete handoff

1. **Evidence accuracy:** [service.py](service.py) places saved `reason_details` into the `evidence` field for several change types. Those details are planning facts, but they are not automatically verified progress or assessment events. Separate them or verify referenced events before presenting them as evidence. The current adapter verifies completed events only; it does not supply verified missed-event or attempt IDs for other reasons.
2. **Current-plan error state:** [ChangesPage.tsx](../../../../frontend/src/features/insights/ChangesPage.tsx) returns the no-plan panel when no plan ID is resolved, even if lookup failed with an authentication, network or server error. Show the error and retry action instead of hiding it.
3. **Preview switching:** aborting a request on plan/format change does not increment the request token. A response that has already advanced to Blob/text processing may still commit an old preview. Invalidate the token on every selection change and test the race.
4. **Browser tests:** [insights.spec.ts](../../../../frontend/tests/insights.spec.ts) contains tests named “NOT RUN” but uses ordinary `test(...)` calls. Those tests are not skipped and the route currently shows the foundation placeholder. Mount the page through Person 1's integration before counting them as passed, or mark them explicitly pending.
5. **Commit scope:** feature code is committed on `person-5` as `a6a1cdc`. That commit also contains the requested team-scope updates in documents 09, 12 and 13; Person 1 should review those coordination changes during integration. This handoff file is a separate, uncommitted addition.

## Verification evidence and limits

- The implementing agent reported **25 passing backend tests** across [test_insights_diff_service.py](../../../tests/test_insights_diff_service.py), [test_insights_api.py](../../../tests/test_insights_api.py) and foundation tests, plus a successful frontend production build. These are handback reports, not an independently completed rerun.
- On an independent read-only attempt, the 9 pure comparison tests completed, then the API test run stalled and was stopped. TypeScript compilation completed, but Vite failed with a local `EPERM` while resolving `frontend/src/main.tsx`. No product-code change was made during that check.
- The Changes screen has not been exercised in the main app. `App.tsx` still mounts the foundation placeholder at `/changes`, and the frontend browser tests do not verify a mounted `ChangesPage` today.
- The existing backend tests use saved-plan fixtures. Person 3's live plan creation and Person 4's complete evidence flow remain integration dependencies.

## Suggested integrated student check

1. Create a goal and generate version 1. Open Changes and confirm it says this is the initial plan, with no fabricated changes.
2. Record a completion or missed study unit, change availability and explicitly generate version 2.
3. Open Changes from the Plan screen. Confirm before/after dates and minutes, both move and resize when applicable, correct deferred/completed classification, unchanged count and honest feasibility figures.
4. Preview CSV and JSON for version 1 and version 2. Download each and confirm the bytes and version match the preview and selection.
5. Attempt another student's plan ID and confirm a 404. Check desktop/mobile layout, keyboard navigation and loading/error states.
6. Once approved, test the version selector and comparison-report download separately. Do not count these as implemented student features until their public API and UI are connected.

## Scope and ownership

Person 5's feature code is confined to `backend/app/features/insights/`, `frontend/src/features/insights/` and uniquely named insights tests. The feature commit also includes the user-requested team-scope edits to documents 09, 12 and 13. Shared routing, contracts, database structure and final integration belong to Person 1. This handoff does not ask other members to change their feature code to compensate for insights defects.
