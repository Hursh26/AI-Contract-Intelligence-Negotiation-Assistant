// The backend has no list-contracts endpoint that is safe to show (it would list everyone's
// contracts, and there is no login yet), so "recent" lives in this browser only.
export type RecentItem = { id: string; filename: string; at: string; risk?: string }

/** How many contracts are remembered. Adding one more drops the oldest. */
export const MAX_RECENT = 10

const KEY = 'fineprint.recent'

function save(items: RecentItem[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(items))
  } catch {
    /* storage can be unavailable (private mode) */
  }
}

/** Same document = same file name, ignoring upper/lower case. */
const sameName = (a: string, b: string) => a.trim().toLowerCase() === b.trim().toLowerCase()

export function getRecent(): RecentItem[] {
  try {
    const items = JSON.parse(localStorage.getItem(KEY) ?? '[]')
    if (!Array.isArray(items)) return []
    // newest first; keep only the newest entry for each file name (also cleans up lists saved before this rule)
    const out: RecentItem[] = []
    for (const r of items as RecentItem[]) {
      if (r && typeof r.id === 'string' && typeof r.filename === 'string' && !out.some((o) => sameName(o.filename, r.filename))) out.push(r)
    }
    return out
  } catch {
    return []
  }
}

/** Uploading the same document again replaces its earlier entry instead of adding another. */
export function pushRecent(item: RecentItem) {
  save([item, ...getRecent().filter((r) => r.id !== item.id && !sameName(r.filename, item.filename))].slice(0, MAX_RECENT))
}

export function updateRecentRisk(id: string, risk: string) {
  save(getRecent().map((r) => (r.id === id ? { ...r, risk } : r)))
}

/** Returns the list after removing one entry. */
export function removeRecent(id: string): RecentItem[] {
  const next = getRecent().filter((r) => r.id !== id)
  save(next)
  return next
}

export function clearRecent(): RecentItem[] {
  save([])
  return []
}
