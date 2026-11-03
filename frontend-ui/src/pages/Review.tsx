import { Fragment, useEffect, useRef, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useContract } from './ContractLayout'
import { NavLink2, RiskTag, Roll, riskBar } from '../components/ui'
import { answer, norm, riskLabel, type Risk } from '../lib/analysis'
import { askContract } from '../lib/api'

type Msg = { q: string; a: string; clauseId?: string; quotes?: string[]; note?: string }

export default function Review() {
  const { contract, analysis: a } = useContract()
  const [busy, setBusy] = useState(false)
  const [params, setParams] = useSearchParams()
  const [filter, setFilter] = useState<Risk | 'all'>('all')
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [q, setQ] = useState('')
  const docRefs = useRef<Record<string, HTMLElement | null>>({})

  const selectedId = params.get('c') ?? a.clauses[0]?.id
  const sel = a.clauses.find((c) => c.id === selectedId) ?? a.clauses[0]
  const list = a.clauses.filter((c) => filter === 'all' || c.risk === filter)

  const select = (id: string, scroll = true) => {
    setParams({ c: id }, { replace: true })
    if (scroll) {
      const p = a.paragraphs.find((p) => p.clauseId === id)
      if (p) docRefs.current[p.id]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  // when arriving from another page with ?c=, bring that clause into view once
  useEffect(() => {
    const id = params.get('c')
    if (id) select(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function ask(e?: FormEvent, text = q) {
    e?.preventDefault()
    const question = text.trim()
    if (!question || busy) return
    setQ('')
    setBusy(true)
    let msg: Msg | null = null
    if (a.source === 'ml') {
      try {
        const r = await askContract(contract.id, question)
        const hit = r.evidence
          .map((ev) => a.clauses.find((c) => norm(c.text).includes(norm(ev.text).slice(0, 40)) || norm(ev.text).includes(norm(c.text).slice(0, 40))))
          .find(Boolean)
        msg = { q: question, a: r.answer, clauseId: hit?.id, quotes: r.evidence.slice(0, 2).map((ev) => ev.text) }
      } catch (err) {
        console.warn('Fineprint: the question service did not answer, using a quick local answer.', err)
      }
    }
    if (!msg) {
      const d = answer(question, a)
      msg = d
        ? { q: question, a: d.text, clauseId: d.clauseId }
        : { q: question, a: 'I could not find anything in this contract that speaks to that. It may simply not be covered, which is worth knowing too.' }
      if (a.source === 'ml') msg.note = 'Our analysis tool could not answer just now, so this is a quick answer from the clauses we found.'
    }
    setMsgs((m) => [...m, msg])
    if (msg.clauseId) select(msg.clauseId)
    setBusy(false)
  }

  const chips = a.clauses.filter((c) => c.risk !== 'low').slice(0, 2).map((c) => `What does the ${c.title.toLowerCase()} clause mean for me?`)

  if (!sel)
    return (
      <main className="mx-auto max-w-3xl px-6 py-20">
        <h1 className="display text-5xl">No standard clauses recognised.</h1>
        <p className="mt-4 text-lg">Here is the full text from your file, so you can still read it.</p>
        <div className="sheet mt-8 p-8">
          {a.paragraphs.map((p) => <p key={p.id} className="doc-p mb-4">{p.text}</p>)}
        </div>
      </main>
    )

  return (
    <main className="mx-auto grid max-w-[1560px] grid-cols-[minmax(0,1fr)] gap-6 px-4 pb-16 pt-6 md:px-8 lg:grid-cols-[290px_minmax(0,1fr)_380px]">
      {/* index */}
      <aside aria-label="Clauses" className="lg:sticky lg:top-[84px] lg:max-h-[calc(100vh-100px)] lg:self-start lg:overflow-auto no-sb">
        <p className="mono text-mute">02 · {list.length} of {a.clauses.length} clauses</p>
        <div role="group" aria-label="Filter by risk" className="mt-3 flex flex-wrap gap-2">
          {(['all', 'high', 'medium', 'low'] as const).map((k) => (
            <button
              key={k}
              aria-pressed={filter === k}
              onClick={() => setFilter(k)}
              className={`mono min-h-11 border-2 border-ink px-3 transition-colors ${filter === k ? 'bg-ink text-lime' : 'bg-transparent hover:bg-lime'}`}
            >
              {k === 'all' ? 'All' : riskLabel[k]}
            </button>
          ))}
        </div>
        <div className="no-sb mt-4 max-h-60 overflow-auto border-t-2 border-ink lg:max-h-none lg:overflow-visible">
          {list.map((c) => (
            <button
              key={c.id}
              data-cursor=""
              aria-pressed={c.id === sel.id}
              onClick={() => select(c.id)}
              className={`row flex w-full items-center gap-3 py-4 pl-3 pr-2 ${c.id === sel.id ? 'on' : ''}`}
              style={{ borderLeft: `6px solid ${riskBar[c.risk]}`, background: 'transparent' }}
            >
              <span className="mono nudge text-mute">{String(c.num).padStart(2, '0')}</span>
              <span className="nudge flex-1 text-[17px] font-bold leading-tight">{c.title}</span>
              <span className="mono text-[10px]" aria-label={`${riskLabel[c.risk]} risk`}>{c.risk === 'high' ? '▲' : c.risk === 'medium' ? '◆' : '●'}</span>
            </button>
          ))}
        </div>
      </aside>

      {/* document */}
      <section aria-label="Contract text" className="min-w-0">
        <p className="mono mb-3 text-mute">The contract text from your file</p>
        <div className="sheet px-6 py-10 md:px-14">
          {a.paragraphs.map((p) => {
            const c = a.clauses.find((c) => c.id === p.clauseId)
            if (!c) return <p key={p.id} className={p.text.length < 60 ? 'doc-p my-4 font-bold' : 'doc-p my-4'}>{p.text}</p>
            const on = c.id === sel.id
            return (
              <Fragment key={p.id}>
              <button
                ref={(el) => { docRefs.current[p.id] = el }}
                onClick={() => select(c.id, false)}
                data-cursor="Explain"
                aria-label={`${c.title}, ${riskLabel[c.risk]} risk. Select to explain.`}
                aria-pressed={on}
                className="doc-p group relative my-3 block w-full border-0 py-1 pl-5 pr-3 text-left transition-colors duration-300"
                style={{
                  borderLeft: `6px solid ${riskBar[c.risk]}`,
                  background: on ? (c.risk === 'high' ? 'rgba(240,57,30,0.14)' : c.risk === 'medium' ? 'rgba(255,176,32,0.25)' : 'rgba(212,255,58,0.45)') : 'transparent',
                  color: 'inherit',
                }}
              >
                <span className="mono absolute -top-1 right-2 translate-y-1 bg-ink px-2 text-[10px] text-lime opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100" aria-hidden>
                  {riskLabel[c.risk]} · {c.title}
                </span>
                {p.text}
              </button>
              {on && (
                <div className="my-3 border-2 border-ink bg-ink p-4 text-paper lg:hidden" style={{ animation: 'noteIn 0.45s cubic-bezier(.2,.8,.2,1)' }}>
                  <div className="flex items-center justify-between gap-3">
                    <RiskTag risk={c.risk} className="!border-paper" />
                    <span className="mono text-paper/60">Clause {c.num}</span>
                  </div>
                  <h3 className="display mt-3 text-[26px] leading-none">{c.title}</h3>
                  <p className="mono mt-4 text-lime">What it means</p>
                  <p className="mt-1 text-[16px] leading-snug">{c.meaning}</p>
                  <p className="mono mt-4 text-lime">Why it matters</p>
                  <p className="mt-1 text-[16px] leading-snug">{c.why}</p>
                  <div className="mt-4 bg-lime p-3 text-ink">
                    <p className="mono">Suggested wording</p>
                    <p className="doc-p mt-1 !text-[16px] !leading-snug">{c.suggestion}</p>
                  </div>
                  <NavLink2 to={`../negotiate#${c.id}`} relative="path" className="btn btn--light mt-4 w-full justify-between no-underline">
                    <Roll>Negotiate this clause</Roll><span aria-hidden>→</span>
                  </NavLink2>
                </div>
              )}
              </Fragment>
            )
          })}
        </div>
      </section>

      {/* inspector */}
      <aside aria-label="Explanation and questions" className="flex flex-col gap-6 lg:sticky lg:top-[84px] lg:max-h-[calc(100vh-100px)] lg:self-start lg:overflow-auto no-sb">
        <div key={sel.id} className="hidden border-2 border-ink bg-ink p-6 text-paper lg:block" style={{ animation: 'noteIn 0.45s cubic-bezier(.2,.8,.2,1)' }}>
          <div className="flex items-center justify-between">
            <RiskTag risk={sel.risk} className="!border-paper" />
            <span className="mono text-paper/60">Clause {sel.num}</span>
          </div>
          <h2 className="display mt-4 text-[34px] leading-[0.98]">{sel.title}</h2>
          <p className="mono mt-6 text-lime">What it means</p>
          <p className="mt-1 text-[17px] leading-snug">{sel.meaning}</p>
          <p className="mono mt-5 text-lime">Why it matters</p>
          <p className="mt-1 text-[17px] leading-snug">{sel.why}</p>
          <div className="mt-6 bg-lime p-4 text-ink">
            <p className="mono">Suggested wording</p>
            <p className="doc-p !text-[17px] !leading-snug mt-1">{sel.suggestion}</p>
          </div>
          <NavLink2 to={`../negotiate#${sel.id}`} relative="path" className="btn btn--light mt-6 w-full justify-between no-underline">
            <Roll>Negotiate this clause</Roll><span aria-hidden>→</span>
          </NavLink2>
        </div>

        <div className="border-2 border-ink bg-sheet p-6">
          <h2 className="display text-[28px]">Ask this contract</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {chips.map((c) => (
              <button key={c} onClick={() => ask(undefined, c)} className="mono min-h-11 border-2 border-ink px-3 text-left normal-case transition-colors hover:bg-lime">{c}</button>
            ))}
          </div>
          <div className="mt-4 space-y-4" aria-live="polite">
            {msgs.map((m, i) => (
              <div key={i} style={{ animation: 'noteIn 0.4s cubic-bezier(.2,.8,.2,1)' }}>
                <p className="mono text-mute">You asked</p>
                <p className="font-bold">{m.q}</p>
                <p className="mt-2 border-l-4 border-lime bg-paper py-2 pl-3 pr-2 leading-snug">{m.a}</p>
                {m.note && <p className="mono mt-2 text-[10px] text-mute">{m.note}</p>}
                {m.quotes?.map((qt, k) => (
                  <p key={k} className="doc-p mt-2 border-l-2 border-ink pl-3 !text-[15px] !leading-snug text-ink/80">
                    <span className="mono mr-2 text-mute">From the contract</span>“{qt.length > 220 ? qt.slice(0, 220) + '…' : qt}”
                  </p>
                ))}
                {m.clauseId && (
                  <button onClick={() => select(m.clauseId!)} className="mono mt-2 min-h-11 border-b-2 border-ink text-ink hover:bg-lime">
                    Source: clause {a.clauses.find((c) => c.id === m.clauseId)?.num} ↗
                  </button>
                )}
              </div>
            ))}
          </div>
          {busy && <p className="mono mt-4 text-mute caret" role="status">Reading the contract</p>}
          <form onSubmit={ask} className="mt-4 flex gap-2">
            <label htmlFor="ask" className="sr-only">Ask a question about this contract</label>
            <input
              id="ask"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Can they end it early?"
              className="min-h-12 min-w-0 flex-1 border-2 border-ink bg-white px-3 text-[16px] placeholder:text-mute focus:bg-lime/30"
            />
            <button type="submit" disabled={busy} className="btn !min-h-12 !px-4" aria-label="Send question"><span aria-hidden>→</span></button>
          </form>
          <p className="mono mt-3 text-[10px] text-mute">{a.source === 'ml' ? 'Answers come from our analysis of your contract. Not legal advice.' : 'These answers are examples for now. Not legal advice.'}</p>
        </div>
      </aside>
    </main>
  )
}
