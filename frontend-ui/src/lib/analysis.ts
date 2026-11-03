// The analysis seam.
//
// The backend can store clauses (PATCH /contracts/{id}/extraction) but the NLP/ML
// pipeline that produces them does not exist yet. Everything the UI shows beyond
// the raw extracted text goes through analyze() below:
//   - if contract.clauses already holds ML output, use it (source: 'ml')
//   - otherwise run a transparent keyword-rule stand-in (source: 'demo')
// When the ML endpoints land, only this file changes.

import type { AnalysisOut, Contract } from './api'

export type Risk = 'high' | 'medium' | 'low'

export type Clause = {
  id: string
  num: number
  title: string
  risk: Risk
  text: string
  meaning: string
  why: string
  suggestion: string
  /** short phrase used in the generated email */
  ask: string
}

export type Para = { id: string; text: string; clauseId?: string }

export type Analysis = {
  source: 'ml' | 'demo'
  paragraphs: Para[]
  clauses: Clause[]
  overall: Risk
  /** 0-100, only when it comes from the real analysis */
  score?: number
  counts: Record<Risk, number>
  /** **bold** marks the phrases that get the highlighter */
  summary: string
  keyTerms: { label: string; value: string }[]
}

type Rule = {
  title: string
  test: RegExp
  build: (t: string) => Pick<Clause, 'risk' | 'meaning' | 'why' | 'suggestion' | 'ask'>
}

const days = (t: string) => [...t.matchAll(/\(?(\d+)\)?\s*(?:business\s+)?days/gi)].map((m) => Number(m[1]))

const RULES: Rule[] = [
  {
    title: 'Termination',
    test: /terminat/i,
    build: (t) => {
      const d = [...new Set(days(t))].sort((a, b) => a - b)
      if (d.length >= 2)
        return {
          risk: 'high',
          meaning: `One side can leave on ${d[0]} days notice. The other needs ${d[d.length - 1]}.`,
          why: 'Unequal notice periods let one party walk away quickly, possibly right before you are paid for work already done.',
          suggestion: 'Either party may terminate on fourteen (14) days written notice. Client shall pay for all work completed up to the termination date.',
          ask: 'equal notice periods for both sides, with payment for completed work',
        }
      return {
        risk: 'medium',
        meaning: 'Describes how and when the contract can be ended.',
        why: 'Check who can end it, with how much notice, and what is owed when it ends.',
        suggestion: 'Either party may terminate on fourteen (14) days written notice. Client shall pay for all work completed up to the termination date.',
        ask: 'clear, equal termination terms and payment for completed work',
      }
    },
  },
  {
    title: 'Non-compete',
    test: /non-?compete|shall not (?:provide|perform|offer) similar|not compete/i,
    build: () => ({
      risk: 'high',
      meaning: 'You cannot work for similar businesses for a period of time.',
      why: 'A broad non-compete can block your other income, during and after this job.',
      suggestion: 'Contractor may provide services to other clients, provided Contractor does not disclose Client confidential information.',
      ask: 'removing or narrowing the non-compete',
    }),
  },
  {
    title: 'Liability',
    test: /indemnif|liabilit/i,
    build: (t) => {
      const open = /without limit|unlimited|all claims|any and all/i.test(t)
      return {
        risk: open ? 'high' : 'medium',
        meaning: open ? 'You would cover the other side for claims and losses, with no cap.' : 'Sets who pays when something goes wrong.',
        why: open ? 'Uncapped liability can exceed what you earn from the whole job.' : 'Look for a cap and for what is excluded.',
        suggestion: 'Contractor\'s total liability under this Agreement shall not exceed the fees paid to Contractor in the preceding twelve (12) months.',
        ask: 'a cap on liability equal to the fees paid',
      }
    },
  },
  {
    title: 'Ownership of work',
    test: /sole property|work product|intellectual property|work made for hire|ownership/i,
    build: (t) => {
      const early = /whether or not|upon creation|regardless of payment/i.test(t)
      return {
        risk: early ? 'high' : 'medium',
        meaning: early ? 'The client owns everything you make the moment you make it.' : 'Says who owns what you create.',
        why: early ? 'This applies even if they never pay you, which removes your leverage in a payment dispute.' : 'Check when ownership transfers and what you keep.',
        suggestion: 'Ownership of work product transfers to Client upon receipt of full payment. Until then Contractor retains all rights.',
        ask: 'ownership transferring only after full payment',
      }
    },
  },
  {
    title: 'Revisions',
    test: /revision/i,
    build: (t) => {
      const open = /until .*(satisf|approv)|unlimited|any number/i.test(t)
      return {
        risk: open ? 'medium' : 'low',
        meaning: open ? 'You keep revising until the client says they are happy.' : 'Sets how many changes the client can request.',
        why: open ? 'With no limit on rounds, the project can drag on without extra pay.' : 'Looks bounded. Confirm the number of rounds.',
        suggestion: 'Contractor shall make up to two (2) rounds of revisions. Further revisions are billed at the agreed hourly rate.',
        ask: 'a cap of two revision rounds',
      }
    },
  },
  {
    title: 'Deposit',
    test: /deposit/i,
    build: () => ({
      risk: 'medium',
      meaning: 'Money you pay up front that may or may not come back.',
      why: 'Check when it is returned, and what can be taken out of it.',
      suggestion: 'The deposit shall be returned within fourteen (14) days of the end of the agreement, with any deductions itemised in writing.',
      ask: 'a clear deadline for returning the deposit',
    }),
  },
  {
    title: 'Payment terms',
    test: /invoice|payment terms|days (?:of|after|from) (?:receipt|delivery|invoice)/i,
    build: (t) => {
      const d = Math.max(0, ...days(t))
      const slow = d >= 45
      return {
        risk: slow ? 'medium' : 'low',
        meaning: d ? `You are paid ${d} days after the trigger described here.` : 'Describes when and how you are paid.',
        why: slow ? `${d} days is long, and you carry the cost of the work until then.` : 'Terms look reasonable. Check late-payment consequences.',
        suggestion: 'Client shall pay 30% on signing, 30% at midpoint, and the balance within fourteen (14) days of each invoice. Late payments accrue interest at 1.5% per month.',
        ask: 'a staged payment schedule with interest on late payments',
      }
    },
  },
  {
    title: 'Confidentiality',
    test: /confidential|non-?disclosure/i,
    build: () => ({
      risk: 'low',
      meaning: 'You must keep the other side\'s non-public information private.',
      why: 'Standard. Check how long it lasts and that it applies both ways.',
      suggestion: 'No change needed. Consider making the obligation mutual.',
      ask: 'making confidentiality mutual',
    }),
  },
  {
    title: 'Governing law',
    test: /governed by|governing law|jurisdiction/i,
    build: () => ({
      risk: 'low',
      meaning: 'Names the legal system that decides any dispute.',
      why: 'Common and usually neutral. It matters mainly if a dispute reaches court far from where you live.',
      suggestion: 'No change needed.',
      ask: 'confirming the governing law',
    }),
  },
  {
    title: 'Scope of work',
    test: /scope of work|schedule a|deliverable/i,
    build: () => ({
      risk: 'low',
      meaning: 'Describes what you are expected to deliver.',
      why: 'A written scope protects you from unlimited extra work. Confirm it matches what you discussed.',
      suggestion: 'No change needed. Confirm the schedule matches your discussions.',
      ask: 'confirming the scope',
    }),
  },
  {
    title: 'Fees',
    test: /fixed fee|\bfees?\b|USD|\$\s?\d|EUR|€|£/i,
    build: () => ({
      risk: 'low',
      meaning: 'States what you are paid for the work.',
      why: 'Check the amount, the currency, and whether expenses are covered.',
      suggestion: 'No change needed. Consider adding that reasonable expenses are reimbursed.',
      ask: 'reimbursement of reasonable expenses',
    }),
  },
  {
    title: 'Auto-renewal',
    test: /automatically renew|renews? automatically|auto-?renew/i,
    build: () => ({
      risk: 'medium',
      meaning: 'The contract continues on its own unless you cancel in time.',
      why: 'Missing a cancellation window can lock you in for another term.',
      suggestion: 'Renewal requires written agreement of both parties. Either party may give notice of non-renewal at least thirty (30) days before the term ends.',
      ask: 'opt-in renewal instead of automatic renewal',
    }),
  },
]

const order: Risk[] = ['high', 'medium', 'low']
export const riskLabel: Record<Risk, string> = { high: 'High', medium: 'Medium', low: 'Low' }

function splitParagraphs(text: string): string[] {
  const blocks = text.split(/\n\s*\n/).map((p) => p.replace(/\s+/g, ' ').trim()).filter(Boolean)
  // some PDFs come out as single newlines; fall back to line splitting
  if (blocks.length < 3) return text.split(/\n/).map((p) => p.trim()).filter((p) => p.length > 0)
  return blocks
}

function keyTerms(text: string): Analysis['keyTerms'] {
  const party = text.match(/between\s+(.+?)\s*\(["“]?(?:Client|Company|Customer)["”]?\)/i)?.[1]
  const amount = text.match(/(?:USD|EUR|GBP|\$|€|£)\s?[\d,]+(?:\.\d+)?/i)?.[0]
  const term = text.match(/(?:\w+\s*\(\d+\)|\d+)\s*(?:months?|years?|weeks?)/i)?.[0]
  const pay = text.match(/(?:within\s+)?(?:\w+\s*\(\d+\)|\d+)\s*days\s+of\s+(?:receipt|invoice|delivery)[^.]*/i)?.[0]
  const dash = '—'
  return [
    { label: 'Other party', value: party ?? dash },
    { label: 'Amount', value: amount ?? dash },
    { label: 'Duration', value: term ?? dash },
    { label: 'Payment', value: pay ? pay.replace(/^within\s+/i, '') : dash },
  ]
}

function fromMl(contract: Contract): Clause[] | null {
  if (!Array.isArray(contract.clauses) || contract.clauses.length === 0) return null
  // The ML pipeline stores { type, text, risk: { level, score, reasons } } (see backend
  // utils/analysis_view.py). It has no plain-language explanation or suggested wording,
  // so those come from our own rules; the risk level is always the ML one.
  const out: Clause[] = []
  for (const raw of contract.clauses as Record<string, unknown>[]) {
    if (!raw || typeof raw !== 'object' || typeof raw.text !== 'string') continue
    const text = raw.text
    const r = (raw.risk && typeof raw.risk === 'object' ? raw.risk : {}) as { level?: unknown; reasons?: unknown }
    const level = String(r.level ?? raw.risk ?? '').toLowerCase()
    const risk: Risk = level === 'high' || level === 'medium' || level === 'low' ? level : 'medium'
    const reasons = Array.isArray(r.reasons) ? r.reasons.map(String) : []
    const title = String(raw.title ?? raw.type ?? 'Clause').replace(/_/g, ' ').replace(/\b\w/g, (ch) => ch.toUpperCase())
    const base = RULES.find((x) => x.test.test(text))?.build(text)
    out.push({
      id: `m${out.length}`,
      num: out.length + 1,
      title,
      risk,
      text,
      meaning: String(raw.meaning ?? base?.meaning ?? 'Part of your contract.'),
      why: String(raw.why ?? base?.why ?? reasons[0] ?? 'Worth a closer read.'),
      suggestion: String(raw.suggestion ?? (risk === 'low' ? 'No change needed.' : base?.suggestion) ?? 'No change needed.'),
      ask: String(raw.ask ?? base?.ask ?? title.toLowerCase()),
    })
  }
  return out.length ? out : null
}

/** Map GET /contracts/{id}/analysis. Risk is the ML one; plain-language wording still comes from our rules. */
function fromRemote(r: AnalysisOut): Clause[] | null {
  const out: Clause[] = []
  for (const c of r.clauses ?? []) {
    if (!c || typeof c.text !== 'string') continue
    const level = String(c.risk_label).toLowerCase()
    const risk: Risk = level === 'high' || level === 'medium' || level === 'low' ? level : 'medium'
    const title = c.category || 'Clause'
    const base = RULES.find((x) => x.test.test(c.text))?.build(c.text)
    out.push({
      id: `m${out.length}`,
      num: out.length + 1,
      title,
      risk,
      text: c.text,
      meaning: base?.meaning ?? 'Part of your contract.',
      why: base?.why ?? c.reasons?.[0] ?? 'Worth a closer read.',
      suggestion: risk === 'low' ? 'No change needed.' : (base?.suggestion ?? 'No change needed.'),
      ask: base?.ask ?? title.toLowerCase(),
    })
  }
  return out.length ? out : null
}

function mlKeyTerms(r: AnalysisOut, text: string): Analysis['keyTerms'] {
  const e = r.entities ?? {}
  const dash = '—'
  const heur = keyTerms(text)
  return [
    { label: 'Other party', value: Object.values(e.parties ?? {})[0]?.name ?? heur[0].value },
    { label: 'Amount', value: e.rent?.value ?? e.deposit?.value ?? e.money_mentions?.[0]?.value ?? heur[1].value },
    { label: 'Key date', value: e.dates?.[0]?.value ?? dash },
    { label: 'Notice period', value: e.notice_periods?.[0]?.value ?? dash },
  ]
}

export const norm = (s: string) => s.toLowerCase().replace(/\s+/g, ' ').trim()

export function analyze(contract: Contract, remote?: AnalysisOut | null): Analysis {
  const text = contract.extracted_text ?? ''
  const mlClauses = (remote && fromRemote(remote)) || fromMl(contract)
  const source: Analysis['source'] = mlClauses ? 'ml' : 'demo'

  const paragraphs: Para[] = splitParagraphs(text).map((t, i) => ({ id: `p${i}`, text: t }))
  let clauses: Clause[] = []

  if (mlClauses) {
    clauses = mlClauses
    for (const c of clauses) {
      const head = norm(c.text).slice(0, 40)
      const p = paragraphs.find((p) => !p.clauseId && norm(p.text).includes(head))
      if (p) p.clauseId = c.id
    }
    clauses.sort((a, b) => order.indexOf(a.risk) - order.indexOf(b.risk) || a.num - b.num)
  } else {
    for (const p of paragraphs) {
      if (p.text.length < 30) continue
      const rule = RULES.find((r) => r.test.test(p.text))
      if (!rule) continue
      const head = p.text.match(/^(\d+)\.\s*(?:[A-Z][\w\s-]{2,30}\.\s*)?/)
      const body = head ? p.text.slice(head[0].length) : p.text
      const id = `c${clauses.length}`
      clauses.push({ id, num: head ? Number(head[1]) : clauses.length + 1, title: rule.title, text: body, ...rule.build(p.text) })
      p.clauseId = id
    }
    clauses.sort((a, b) => order.indexOf(a.risk) - order.indexOf(b.risk) || a.num - b.num)
  }

  const counts: Record<Risk, number> = { high: 0, medium: 0, low: 0 }
  for (const c of clauses) counts[c.risk]++
  const rs = source === 'ml' ? remote?.risk_summary : undefined
  const lvl = rs?.level?.toLowerCase()
  const overall: Risk =
    lvl === 'high' || lvl === 'medium' || lvl === 'low'
      ? lvl
      : counts.high >= 2 ? 'high' : counts.high >= 1 || counts.medium >= 2 ? 'medium' : 'low'

  let summary: string
  if (clauses.length === 0) {
    summary = 'We could not recognise any standard clauses in this text. The full text is on the **Review** page so you can still read it yourself.'
  } else {
    const top = clauses.filter((c) => c.risk === 'high').slice(0, 3)
    const n = (k: number, one: string, many: string) => `${k} ${k === 1 ? one : many}`
    const risk = counts.high
      ? `**${counts.high === 1 ? '1 carries' : `${counts.high} carry`} real risk**`
      : '**None looks seriously risky**'
    const lead = `We found **${n(clauses.length, 'clause', 'clauses')}** worth knowing about. ${risk}${counts.medium ? ` and ${n(counts.medium, 'deserves', 'deserve')} a second look` : ''}.`
    const points = top.map((c) => `**${c.title}.** ${c.meaning}`).join(' ')
    summary = [lead, points].filter(Boolean).join(' ')
  }

  return {
    source,
    paragraphs,
    clauses,
    overall,
    score: rs?.overall_score,
    counts,
    summary,
    keyTerms: remote && source === 'ml' ? mlKeyTerms(remote, text) : keyTerms(text),
  }
}

// ── "Ask about this contract": keyword overlap against the clauses we found ──
const SYNONYMS: Record<string, string> = {
  end: 'terminat', quit: 'terminat', cancel: 'terminat', leave: 'terminat', fire: 'terminat',
  paid: 'payment', pay: 'payment', money: 'payment', invoice: 'payment', fee: 'fees',
  own: 'ownership', owns: 'ownership', keep: 'ownership', rights: 'ownership', copyright: 'ownership',
  sue: 'liability', liable: 'liability', responsible: 'liability', damages: 'liability',
  compete: 'non-compete', competitor: 'non-compete', secret: 'confidential', private: 'confidential',
  law: 'governing', court: 'governing', changes: 'revision', edits: 'revision',
}
const STOP = new Set(['what', 'when', 'will', 'does', 'with', 'this', 'that', 'they', 'them', 'have', 'from', 'about', 'can', 'the', 'and', 'for', 'are', 'not', 'how', 'who', 'would', 'could', 'should', 'there', 'their'])

export function answer(question: string, a: Analysis): { text: string; clauseId: string } | null {
  const words = question.toLowerCase().match(/[a-z-]{3,}/g)?.filter((w) => !STOP.has(w)) ?? []
  const keys = new Set(words.flatMap((w) => [w, SYNONYMS[w]].filter(Boolean) as string[]))
  let best: { c: Clause; score: number } | null = null
  for (const c of a.clauses) {
    const hay = `${c.title} ${c.text} ${c.meaning} ${c.why}`.toLowerCase()
    let score = 0
    for (const k of keys) if (hay.includes(k)) score += c.title.toLowerCase().includes(k) ? 3 : 1
    if (score > (best?.score ?? 0)) best = { c, score }
  }
  if (!best) return null
  const { c } = best
  return { text: `${c.meaning} ${c.why}`.trim(), clauseId: c.id }
}
