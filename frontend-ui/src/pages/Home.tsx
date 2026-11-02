import { useEffect, useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadContract, friendlyError } from '../lib/api'
import { MAX_RECENT, clearRecent, getRecent, removeRecent, type RecentItem } from '../lib/recent'
import { SAMPLE_NAME, SAMPLE_TEXT } from '../lib/sample'
import { Magnetic, NavLink2, Reveal, RiskTag, Roll, Split, Wordmark, useInView } from '../components/ui'
import type { Risk } from '../lib/analysis'

const MAX_MB = 10
const OK_EXT = ['.pdf', '.docx', '.txt']

const CLAUSE_WORDS = ['Termination', 'Indemnity', 'Ownership', 'Non-compete', 'Payment terms', 'Auto-renewal', 'Liability cap', 'Governing law', 'Confidentiality', 'Revisions']

const STEPS = [
  { n: '01', t: 'Understand', d: 'A plain-English summary, the key amounts and dates, and a risk level for every clause.' },
  { n: '02', t: 'Question', d: 'Ask in your own words. Every answer points back to the sentence it came from.' },
  { n: '03', t: 'Negotiate', d: 'Accept or reject suggested wording, then take away a marked-up copy and a ready-to-send email.' },
]

const DEMO = [
  { phrase: 'whether or not completed or paid for', note: 'You would lose ownership of your work even if the client never pays you.' },
  { phrase: 'seven (7) days written notice', note: 'They can leave in 7 days. You are held to 30. Unequal exits favour whoever wrote the contract.' },
  { phrase: 'without limit', note: 'No cap on what you could owe. One claim could exceed the whole fee.' },
]

export default function Home() {
  const nav = useNavigate()
  const input = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [shakeKey, setShakeKey] = useState(0)
  const [demo, setDemo] = useState(0)
  const [recent, setRecent] = useState<RecentItem[]>(getRecent)
  const [confirmClear, setConfirmClear] = useState(false)
  // keep several open tabs in step with each other
  useEffect(() => {
    const sync = () => setRecent(getRecent())
    window.addEventListener('storage', sync)
    return () => window.removeEventListener('storage', sync)
  }, [])
  // "Sure? Clear all" only stays armed for a few seconds so a stray click later cannot wipe the list.
  useEffect(() => {
    if (!confirmClear) return
    const t = setTimeout(() => setConfirmClear(false), 4000)
    return () => clearTimeout(t)
  }, [confirmClear])
  const [demoRef, demoSeen] = useInView<HTMLDivElement>(0.3)

  async function send(file: File) {
    setError(null)
    const ext = '.' + (file.name.split('.').pop() ?? '').toLowerCase()
    const problem = !OK_EXT.includes(ext)
      ? `“${file.name}” is not a supported file. Please use a PDF, Word document or text file.`
      : file.size === 0
        ? 'That file is empty.'
        : file.size > MAX_MB * 1024 * 1024
          ? `That file is over ${MAX_MB} MB.`
          : null
    if (problem) return fail(problem)
    setBusy(true)
    try {
      const c = await uploadContract(file)
      nav(`/c/${c.id}/reading`, { viewTransition: true })
    } catch (e) {
      setBusy(false)
      fail(friendlyError(e))
    }
  }
  function fail(msg: string) {
    setError(msg)
    setShakeKey((k) => k + 1)
  }
  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDrag(false)
    const f = e.dataTransfer.files?.[0]
    if (f) void send(f)
  }

  return (
    <div>
      {/* ── hero ── */}
      <section className="relative overflow-hidden bg-ink text-paper">
        <header className="mx-auto flex max-w-[1320px] flex-wrap items-center justify-between gap-4 px-6 py-6 md:px-10">
          <Wordmark dark />
          <nav className="mono -mx-2 flex flex-wrap gap-x-2 text-paper/70 sm:gap-x-6">
            <a href="#how" className="flex min-h-11 items-center px-2 hover:text-lime"><Roll>How it works</Roll></a>
            <a href="#spot" className="flex min-h-11 items-center px-2 hover:text-lime"><Roll>See it spot risk</Roll></a>
            <a href="#recent" className="flex min-h-11 items-center px-2 hover:text-lime"><Roll>Recent</Roll></a>
          </nav>
        </header>

        <div className="mx-auto max-w-[1320px] px-6 pb-20 pt-10 md:px-10 md:pt-16">
          <Split
            text="Read the fine print. Before it reads you."
            hl={['fine', 'print']}
            className="display text-[clamp(52px,10.5vw,156px)] max-w-[12ch]"
          />
          <Reveal delay={500} className="mt-8 max-w-xl text-lg leading-relaxed text-paper/75">
            <p>
              Upload a contract. We translate it into plain language, mark the clauses that can hurt you, answer your questions, and draft the changes to ask for.
            </p>
          </Reveal>

          {/* drop zone */}
          <Reveal delay={650} className="mt-12">
            <div
              key={shakeKey}
              role="group"
              aria-label="Upload a contract"
              data-cursor={busy ? '' : 'Drop'}
              onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
              onDragLeave={() => setDrag(false)}
              onDrop={onDrop}
              className={`relative border-2 px-6 py-14 text-center transition-colors duration-300 md:py-20 ${error ? 'shake' : ''} ${drag ? 'border-lime bg-lime text-ink' : 'border-paper/40 text-paper'}`}
              style={{ backgroundImage: drag ? undefined : 'repeating-linear-gradient(135deg, transparent 0 11px, rgba(243,243,238,0.05) 11px 12px)' }}
            >
              {['left-0 top-0 border-l-4 border-t-4', 'right-0 top-0 border-r-4 border-t-4', 'bottom-0 left-0 border-b-4 border-l-4', 'bottom-0 right-0 border-b-4 border-r-4'].map((c) => (
                <span key={c} aria-hidden className={`absolute h-5 w-5 ${c} ${drag ? 'border-ink' : 'border-lime'}`} style={{ margin: -2 }} />
              ))}
              <div className="display text-[clamp(30px,5vw,64px)]">{busy ? 'Uploading' : drag ? 'Let go' : 'Drop a contract here'}{busy && <span className="caret" />}</div>
              <p className="mono mt-3 opacity-70">PDF, Word or text file · up to {MAX_MB} MB</p>
              <div className="mt-8 flex flex-wrap items-center justify-center gap-x-8 gap-y-5">
                <Magnetic>
                  <button className="btn" disabled={busy} onClick={() => input.current?.click()}>
                    <Roll>Choose a file</Roll><span aria-hidden>↑</span>
                  </button>
                </Magnetic>
                <button
                  disabled={busy}
                  onClick={() => void send(new File([SAMPLE_TEXT], SAMPLE_NAME, { type: 'text/plain' }))}
                  className="mono min-h-11 border-b-2 border-current bg-transparent px-0 text-current hover:text-lime"
                  style={{ color: drag ? '#0f110e' : undefined }}
                >
                  <Roll>or try a sample contract →</Roll>
                </button>
              </div>
              <input
                ref={input}
                type="file"
                accept=".pdf,.docx,.txt"
                hidden
                aria-label="Choose a contract file"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  e.target.value = ''
                  if (f) void send(f)
                }}
              />
            </div>
            <div role="alert" aria-live="assertive" className="min-h-8">
              {error && (
                <p className="mt-4 flex gap-3 border-l-4 border-pen bg-pen/10 py-3 pl-4 pr-3 text-[15px] text-paper">
                  <span className="mono text-pen" aria-hidden>▲ Stopped</span>
                  <span>{error}</span>
                </p>
              )}
            </div>
            <p className="mono mt-4 text-paper/55">Your file stays private · No account needed · Information, not legal advice</p>
          </Reveal>
        </div>

        {/* marquee */}
        <div className="marquee border-y-2 border-ink bg-lime py-4 text-ink" data-cursor="Slow">
          <div className="marquee-track" aria-hidden>
            {[0, 1].map((k) => (
              <div key={k} className="flex shrink-0 items-center">
                {CLAUSE_WORDS.map((w, i) => (
                  <span key={w} className="display flex items-center gap-8 pr-8 text-[clamp(28px,4vw,52px)]">
                    <span className={i % 3 === 0 ? 'line-through decoration-pen decoration-[5px]' : ''}>{w}</span>
                    <span className="text-pen">✺</span>
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── how it reads ── */}
      <section id="how" className="mx-auto max-w-[1320px] px-6 py-24 md:px-10">
        <Split as="h2" text="Three moves. No jargon." hl={['jargon.']} className="display text-[clamp(40px,7vw,104px)]" />
        <div className="mt-14 border-t-2 border-ink">
          {STEPS.map((s, i) => (
            <Reveal key={s.n} delay={i * 90}>
              <div className="row flex flex-wrap items-baseline gap-x-10 gap-y-2 py-8" data-cursor="">
                <span className="mono nudge w-12 text-mute">{s.n}</span>
                <span className="display nudge text-[clamp(34px,6vw,84px)]">{s.t}</span>
                <span className="nudge flex-1 basis-80 text-lg leading-snug text-ink/80">{s.d}</span>
                <span className="arrow display hidden text-5xl md:block" aria-hidden>→</span>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ── hover demo ── */}
      <section id="spot" className="border-y-2 border-ink bg-sheet">
        <div className="mx-auto grid max-w-[1320px] gap-12 px-6 py-24 md:px-10 lg:grid-cols-[1.3fr_1fr]">
          <div ref={demoRef} className={demoSeen ? 'in' : ''}>
            <p className="mono text-mute">Hover the red lines</p>
            <div className="sheet mt-4 p-8 md:p-12">
              <p className="doc-p">
                <b>5. Ownership.</b> All work product,{' '}
                <button className={`pen ${demo === 0 ? 'on' : ''}`} onMouseEnter={() => setDemo(0)} onFocus={() => setDemo(0)} data-cursor="Why?">whether or not completed or paid for</button>
                , is the sole property of Client upon creation.
              </p>
              <p className="doc-p mt-6">
                <b>7. Termination.</b> Client may terminate this Agreement on{' '}
                <button className={`pen ${demo === 1 ? 'on' : ''}`} onMouseEnter={() => setDemo(1)} onFocus={() => setDemo(1)} data-cursor="Why?">seven (7) days written notice</button>
                . Contractor may terminate on thirty (30) days.
              </p>
              <p className="doc-p mt-6">
                <b>8. Liability.</b> Contractor shall indemnify Client against all claims,{' '}
                <button className={`pen ${demo === 2 ? 'on' : ''}`} onMouseEnter={() => setDemo(2)} onFocus={() => setDemo(2)} data-cursor="Why?">without limit</button>
                .
              </p>
            </div>
          </div>
          <div className="flex flex-col justify-center" aria-live="polite">
            <p className="mono text-pen-d">▲ Margin note {String(demo + 1).padStart(2, '0')}</p>
            <p key={demo} className="reveal in display mt-4 text-[clamp(28px,3.4vw,46px)] leading-[1.02]" style={{ animation: 'noteIn 0.5s cubic-bezier(.2,.8,.2,1)' }}>
              {DEMO[demo].note}
            </p>
            <p className="mono mt-6 text-mute">What you will see on every contract</p>
          </div>
        </div>
      </section>

      {/* ── recent ── */}
      <section id="recent" className="mx-auto max-w-[1320px] px-6 py-24 md:px-10">
        <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
          <h2 className="display text-[clamp(34px,5vw,72px)]">Recent</h2>
          {recent.length > 0 && (
            <div className="flex items-center gap-4">
              <span className="mono text-mute">{recent.length} of {MAX_RECENT} saved</span>
              <button
                onClick={() => {
                  if (!confirmClear) return setConfirmClear(true)
                  setRecent(clearRecent())
                  setConfirmClear(false)
                }}
                data-cursor=""
                className={`mono min-h-11 border-2 px-4 font-bold transition-colors ${confirmClear ? 'border-pen-d bg-pen-d text-white' : 'border-ink bg-transparent hover:bg-lime'}`}
              >
                {confirmClear ? 'Sure? Clear all' : 'Clear all'}
              </button>
            </div>
          )}
        </div>
        <div className="mt-8 border-t-2 border-ink">
          {recent.length === 0 && <p className="mono py-8 text-mute">Nothing yet. Contracts you review appear here, on this device only.</p>}
          {recent.map((r) => (
            <div key={r.id} className="flex items-stretch">
              <NavLink2 to={`/c/${r.id}`} data-cursor="Open" className="row flex min-w-0 flex-1 flex-wrap items-center justify-between gap-x-4 gap-y-2 py-6 text-ink no-underline">
                <span className="nudge display min-w-0 text-[clamp(22px,3vw,40px)] [overflow-wrap:anywhere]">{r.filename}</span>
                <span className="flex items-center gap-4">
                  <span className="mono text-mute">{new Date(r.at).toLocaleDateString()} · {new Date(r.at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>
                  {r.risk && <RiskTag risk={r.risk as Risk} />}
                  <span className="arrow display hidden text-3xl sm:block" aria-hidden>→</span>
                </span>
              </NavLink2>
              <button
                aria-label={`Remove ${r.filename} from recent`}
                title="Remove from this list"
                data-cursor="Remove"
                onClick={() => setRecent(removeRecent(r.id))}
                className="grid w-12 shrink-0 place-items-center border-b-2 border-ink bg-transparent text-ink transition-colors hover:bg-pen-d hover:text-white sm:w-14"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19" /></svg>
              </button>
            </div>
          ))}
        </div>
        {recent.length > 0 && (
          <p className="mono mt-4 max-w-2xl text-[11px] leading-relaxed text-mute">
            We keep your last {MAX_RECENT}. Older ones drop off on their own. Removing a contract only clears it from this list on this device.
          </p>
        )}
      </section>

      <footer className="bg-ink px-6 py-10 text-paper/70 md:px-10">
        <div className="mx-auto flex max-w-[1320px] flex-wrap items-center justify-between gap-4">
          <Wordmark dark />
          <p className="mono">Fineprint explains contracts. It is not a law firm and does not give legal advice.</p>
        </div>
      </footer>
    </div>
  )
}
