import { useNavigate } from 'react-router-dom'
import { useContract } from './ContractLayout'
import { CountUp, Marked, NavLink2, Reveal, RiskTag, Roll, riskBar, Magnetic } from '../components/ui'
import { riskLabel } from '../lib/analysis'

export default function Overview() {
  const { contract, analysis: a } = useContract()
  const nav = useNavigate()
  const title = contract.filename.replace(/\.[^.]+$/, '').replace(/[-_]+/g, ' ')
  const first = a.clauses.filter((c) => c.risk !== 'low').slice(0, 4)
  const assessed = a.clauses.length > 0

  return (
    <main className="mx-auto max-w-[1400px] px-4 pb-28 pt-10 sm:px-6 md:px-10">
      <div className="grid grid-cols-[minmax(0,1fr)] gap-12 lg:grid-cols-[1.5fr_1fr]">
        <div>
          <p className="mono text-mute">01 · Overview · {contract.filename}</p>
          <h1 className="display mt-4 text-[clamp(40px,6.4vw,104px)] capitalize">{title}</h1>
          <Reveal delay={200}>
            <p className="mt-10 max-w-[34ch] text-[clamp(22px,2.6vw,36px)] font-medium leading-[1.22] md:max-w-[40ch]">
              <Marked text={a.summary} />
            </p>
          </Reveal>
        </div>

        {/* verdict */}
        <aside className="relative min-w-0 self-start overflow-hidden border-2 border-ink bg-sheet p-6 shadow-[8px_8px_0_#0f110e] sm:p-8">
          <p className="mono text-mute">Overall risk</p>
          <div className="mt-2 flex items-end gap-4">
            <span className="display text-[clamp(90px,10vw,150px)] leading-none">{assessed ? <CountUp to={a.score ?? a.counts.high * 10 + a.counts.medium * 4} /> : '—'}</span>
            {assessed && <span className="mono pb-4 text-mute">{a.score !== undefined ? '/ 100 · risk score' : '/ 100 · example score'}</span>}
          </div>
          <div className="my-3 h-14">
            <span className={`stamp text-[22px] ${!assessed ? 'text-mute' : a.overall === 'high' ? 'text-pen-d' : a.overall === 'medium' ? 'text-[#a96800]' : 'text-ink'}`} style={{ animationDelay: '0.5s' }}>
              {assessed ? `${riskLabel[a.overall]} risk` : 'Not rated'}
            </span>
          </div>
          {/* one tick per clause */}
          <div className="mt-6 flex h-12 gap-[3px]" role="list" aria-label="Clauses by risk">
            {a.clauses.map((c, i) => (
              <button
                key={c.id}
                role="listitem"
                data-cursor={c.title}
                aria-label={`${c.title}, ${riskLabel[c.risk]} risk`}
                onClick={() => nav(`review?c=${c.id}`, { viewTransition: true })}
                className="min-w-[10px] flex-1 origin-bottom border-0 transition-transform duration-300 hover:scale-y-[1.35]"
                style={{ background: riskBar[c.risk], animation: 'noteIn 0.5s both', animationDelay: `${300 + i * 45}ms` }}
              />
            ))}
          </div>
          <dl className="mono mt-6 grid grid-cols-3 gap-2 text-center">
            {(['high', 'medium', 'low'] as const).map((r) => (
              <div key={r} className="border-2 border-ink py-2">
                <dt className="text-[10px] text-mute">{riskLabel[r]}</dt>
                <dd className="display text-3xl"><CountUp to={a.counts[r]} /></dd>
              </div>
            ))}
          </dl>
        </aside>
      </div>

      {/* key terms */}
      <section className="mt-24" aria-label="Key terms">
        <p className="mono text-mute">Key facts we found</p>
        <dl className="mt-4 grid border-t-2 border-ink sm:grid-cols-2 lg:grid-cols-4">
          {a.keyTerms.map((k, i) => (
            <Reveal key={k.label} delay={i * 70} className="min-w-0 border-b-2 border-ink py-6 sm:pr-6 lg:border-r-2 lg:px-6 lg:first:pl-0 lg:last:border-r-0">
              <dt className="mono text-mute">{k.label}</dt>
              <dd className="display mt-2 break-words text-[clamp(22px,2.4vw,34px)] leading-[1.05]">{k.value}</dd>
            </Reveal>
          ))}
        </dl>
      </section>

      {/* look at first */}
      <section className="mt-24" aria-label="Look at these first">
        <h2 className="display text-[clamp(34px,5vw,72px)]">Look at these first</h2>
        <div className="mt-8 border-t-2 border-ink">
          {first.length === 0 && <p className="mono py-8 text-mute">Nothing flagged. You can still read the whole contract in Review.</p>}
          {first.map((c) => (
            <NavLink2 key={c.id} to={`review?c=${c.id}`} data-cursor="Open" className="row flex flex-wrap items-center gap-x-8 gap-y-3 py-7 text-ink no-underline">
              <span className="mono nudge w-10 text-mute">{String(c.num).padStart(2, '0')}</span>
              <RiskTag risk={c.risk} />
              <span className="nudge display text-[clamp(26px,3.6vw,52px)]">{c.title}</span>
              <span className="nudge flex-1 basis-72 text-lg leading-snug text-ink/80">{c.meaning}</span>
              <span className="arrow display text-4xl" aria-hidden>→</span>
            </NavLink2>
          ))}
        </div>
        <div className="mt-12 flex flex-wrap items-center gap-6">
          <Magnetic><NavLink2 to="review" className="btn no-underline"><Roll>{assessed ? `Review all ${a.clauses.length} clauses` : 'Read the full text'}</Roll><span aria-hidden>→</span></NavLink2></Magnetic>
          <NavLink2 to="negotiate" className="mono min-h-11 border-b-2 border-ink py-3 text-ink no-underline"><Roll>Go straight to negotiating</Roll></NavLink2>
        </div>
        <p className="mono mt-10 max-w-xl text-mute">Information to help you read the contract, not legal advice. For anything important, have a lawyer look at it.</p>
      </section>
    </main>
  )
}
