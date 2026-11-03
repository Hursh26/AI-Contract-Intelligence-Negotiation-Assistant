import { useEffect, useMemo, useState } from 'react'
import { NavLink, Navigate, Outlet, useOutletContext, useParams } from 'react-router-dom'
import { ApiError, friendlyError, getAnalysis, getContract, type AnalysisOut, type Contract } from '../lib/api'
import { analyze, type Analysis } from '../lib/analysis'
import { updateRecentRisk } from '../lib/recent'
import { NavLink2, Wordmark } from '../components/ui'

export type ContractCtx = { contract: Contract; analysis: Analysis }
export const useContract = () => useOutletContext<ContractCtx>()

const TABS = [
  { to: '', n: '01', label: 'Overview', end: true },
  { to: 'review', n: '02', label: 'Review', end: false },
  { to: 'negotiate', n: '03', label: 'Negotiate', end: false },
]

export default function ContractLayout() {
  const { id = '' } = useParams()
  const [contract, setContract] = useState<Contract | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [remote, setRemote] = useState<AnalysisOut | null>(null)

  useEffect(() => {
    let live = true
    setContract(null)
    setRemote(null)
    setError(null)
    ;(async () => {
      try {
        const c = await getContract(id)
        // Only analysed contracts have clauses stored; older backends have no /analysis at all.
        let r: AnalysisOut | null = null
        if (Array.isArray(c.clauses)) {
          try {
            r = await getAnalysis(id)
          } catch (e) {
            console.warn('Fineprint: analysis not available, using the built-in preview instead.', e)
          }
        }
        if (live) {
          setRemote(r)
          setContract(c)
        }
      } catch (e) {
        if (live) setError(e instanceof ApiError ? e : new ApiError(500, 'unknown'))
      }
    })()
    return () => { live = false }
  }, [id])

  const analysis = useMemo(() => (contract ? analyze(contract, remote) : null), [contract, remote])
  useEffect(() => {
    if (analysis && contract && analysis.clauses.length) updateRecentRisk(contract.id, analysis.overall)
  }, [analysis, contract])

  if (error)
    return (
      <div className="grid min-h-screen place-items-center bg-ink p-8 text-paper">
        <div className="max-w-lg">
          <p className="mono text-pen">▲ {error.status === 404 ? 'Not found' : 'Problem'}</p>
          <h1 className="display mt-3 text-5xl">{friendlyError(error)}</h1>
          <NavLink2 to="/" className="btn mt-8 no-underline"><span>← Upload another</span></NavLink2>
        </div>
      </div>
    )
  if (!contract || !analysis)
    return (
      <div className="grid min-h-screen place-items-center bg-ink text-lime">
        <p className="mono caret" role="status">Opening contract</p>
      </div>
    )
  // Backends differ on the status word after extraction ("processed" / "extracted"), so key off the text itself.
  if (!contract.extracted_text) return <Navigate to={`/c/${id}/reading`} replace />

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b-2 border-ink bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-x-6 gap-y-0 px-4 py-2 sm:px-6 md:px-10 md:py-3">
          <div className="flex items-center gap-6">
            <Wordmark />
            <span className="mono hidden max-w-[28ch] truncate text-mute md:block" title={contract.filename}>{contract.filename}</span>
          </div>
          <nav aria-label="Steps" className="-mx-2 flex sm:mx-0">
            {TABS.map((t) => (
              <NavLink
                key={t.n}
                to={t.to}
                end={t.end}
                viewTransition
                data-cursor=""
                className={({ isActive }) =>
                  `mono group relative flex min-h-11 items-center gap-1.5 px-2.5 no-underline transition-colors sm:gap-2 sm:px-4 ${isActive ? 'text-ink' : 'text-mute hover:text-ink'}`
                }
              >
                {({ isActive }) => (
                  <>
                    <span className="text-[10px]">{t.n}</span>
                    <span className={isActive ? 'hl in' : ''}>{t.label}</span>
                    <span aria-hidden className={`absolute inset-x-3 bottom-0 h-[3px] origin-left bg-ink transition-transform duration-300 ${isActive ? 'scale-x-100' : 'scale-x-0 group-hover:scale-x-100'}`} />
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <div className="mono border-b-2 border-ink bg-lime px-4 py-1.5 text-center text-[10px] leading-snug text-ink sm:text-[11px]">
        {analysis.source === 'demo'
          ? 'Early preview · The contract text is yours. The risk ratings, answers and suggestions are examples while we finish building the full analysis'
          : 'Early preview · Risk ratings and answers come from our analysis. The plain-language explanations and suggested wording are examples for now'}
      </div>
      <Outlet context={{ contract, analysis } satisfies ContractCtx} />
    </div>
  )
}
