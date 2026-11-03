import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { analyzeContract, extractContract, friendlyError } from '../lib/api'
import { pushRecent } from '../lib/recent'
import { NavLink2, Wordmark } from '../components/ui'

const STEPS = ['File received', 'Reading every page', 'Finding clauses and risks', 'Writing your summary']
const LINES = [92, 100, 78, 96, 64, 100, 88, 70, 98, 54, 94, 82, 100, 60]

export default function Reading() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const started = useRef(false)
  const [stage, setStage] = useState(1)
  const [error, setError] = useState<string | null>(null)

  // Stage 1 is the real POST /extract. Stages 2-3 are the local analysis, paced so the work is visible.
  useEffect(() => {
    if (started.current) return
    started.current = true
    ;(async () => {
      try {
        const c = await extractContract(id)
        pushRecent({ id: c.id, filename: c.filename, at: new Date().toISOString() })
        setStage(2)
        await new Promise((r) => setTimeout(r, 700))
        setStage(3)
        // Real analysis (backend `develop`). If it is unavailable or the ML service is down we carry on:
        // the contract text is already saved and the app falls back to the built-in preview.
        await Promise.all([
          analyzeContract(id).catch((e) => console.warn('Fineprint: analysis unavailable, continuing with the preview.', e)),
          new Promise((r) => setTimeout(r, 800)),
        ])
        setStage(4)
        await new Promise((r) => setTimeout(r, 500))
        nav(`/c/${id}`, { replace: true, viewTransition: true })
      } catch (e) {
        setError(friendlyError(e))
      }
    })()
  }, [id, nav])

  const pct = Math.min(100, Math.round((stage / STEPS.length) * 100))
  const lit = Math.round((stage / STEPS.length) * LINES.length)

  return (
    <div className="min-h-screen bg-ink text-paper">
      <div className="mx-auto max-w-[1320px] px-6 py-6 md:px-10"><Wordmark dark /></div>
      <main className="mx-auto grid max-w-[1320px] gap-14 px-6 pb-20 pt-6 md:px-10 lg:grid-cols-2">
        <div>
          <p className="mono text-lime">{error ? '▲ Stopped' : 'Reading your contract'}</p>
          {error ? (
            <>
              <h1 className="display mt-4 text-[clamp(36px,5vw,72px)]" role="alert">{error}</h1>
              <NavLink2 to="/" className="btn mt-10 no-underline"><span>← Try another file</span></NavLink2>
            </>
          ) : (
            <>
              <div className="display mt-4 text-[clamp(110px,20vw,280px)] leading-[0.85] tabular-nums" aria-label={`${pct} percent`}>
                {pct}<span className="text-lime">%</span>
              </div>
              <ol className="mono mt-10 space-y-3">
                {STEPS.map((s, i) => {
                  const done = stage > i
                  const active = stage === i
                  return (
                    <li key={s} className={`flex items-center gap-3 transition-opacity duration-500 ${done || active ? 'opacity-100' : 'opacity-35'}`}>
                      <span className={`grid h-5 w-5 place-items-center border-2 ${done ? 'border-lime bg-lime text-ink' : 'border-paper'}`} aria-hidden>{done ? '✓' : ''}</span>
                      <span className={active ? `text-lime ${active ? 'caret' : ''}` : ''}>{s}</span>
                    </li>
                  )
                })}
              </ol>
            </>
          )}
        </div>

        <div className="relative hidden self-start overflow-hidden border-2 border-paper/40 p-10 lg:block scan" aria-hidden>
          <div className="space-y-5">
            {LINES.map((w, i) => (
              <div key={i} className="h-3 bg-paper/15" style={{ width: `${w}%` }}>
                <div className="h-full bg-lime transition-[width] duration-700" style={{ width: i < lit && i % 3 === 1 ? '100%' : '0%', transitionDelay: `${i * 60}ms` }} />
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
