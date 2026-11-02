import { useEffect, useRef, useState, type ReactNode, type CSSProperties } from 'react'
import { Link, type LinkProps } from 'react-router-dom'
import type { Risk } from '../lib/analysis'
import { riskLabel } from '../lib/analysis'

/** Adds .in once the element scrolls into view (or immediately if motion is reduced). */
export function useInView<T extends HTMLElement>(threshold = 0.2) {
  const ref = useRef<T>(null)
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (typeof IntersectionObserver === 'undefined') {
      setSeen(true)
      return
    }
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setSeen(true)
          io.disconnect()
        }
      },
      { threshold },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [threshold])
  return [ref, seen] as const
}

export function Reveal({ children, delay = 0, className = '', as: Tag = 'div' }: { children: ReactNode; delay?: number; className?: string; as?: 'div' | 'section' | 'li' | 'p' }) {
  const [ref, seen] = useInView<HTMLDivElement>()
  return (
    <Tag ref={ref as never} className={`reveal ${seen ? 'in' : ''} ${className}`} style={{ '--d': `${delay}ms` } as CSSProperties}>
      {children}
    </Tag>
  )
}

/** Headline that slides up word by word. Wrap emphasised words in <mark class="hl"> via the `hl` list. */
export function Split({ text, hl = [], className = '', as: Tag = 'h1' }: { text: string; hl?: string[]; className?: string; as?: 'h1' | 'h2' | 'p' }) {
  const [ref, seen] = useInView<HTMLElement>(0.1)
  const words = text.split(' ')
  return (
    <Tag ref={ref as never} className={`${seen ? 'in' : ''} ${className}`} aria-label={text}>
      {words.map((w, i) => (
        <span key={i} aria-hidden className="word" style={{ '--i': i } as CSSProperties}>
          <span>{hl.includes(w.replace(/[.,]/g, '')) ? <mark className="hl">{w}</mark> : w}&nbsp;</span>
        </span>
      ))}
    </Tag>
  )
}

/** Label that rolls up to a duplicate on hover. */
export function Roll({ children }: { children: string }) {
  return (
    <span className="roll" aria-label={children}>
      <span aria-hidden>{children}</span>
      <span aria-hidden>{children}</span>
    </span>
  )
}

/** Pulls its child toward the pointer, springs back on leave. Off on touch. */
export function Magnetic({ children, strength = 0.35 }: { children: ReactNode; strength?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const fine = typeof window !== 'undefined' && window.matchMedia('(pointer: fine)').matches
  return (
    <div
      ref={ref}
      style={{ display: 'inline-block', transition: 'transform 0.5s cubic-bezier(.2,.8,.2,1)' }}
      onPointerMove={(e) => {
        if (!fine || !ref.current) return
        const r = ref.current.getBoundingClientRect()
        const x = (e.clientX - (r.left + r.width / 2)) * strength
        const y = (e.clientY - (r.top + r.height / 2)) * strength
        ref.current.style.transition = 'transform 0.1s linear'
        ref.current.style.transform = `translate(${x}px, ${y}px)`
      }}
      onPointerLeave={() => {
        if (!ref.current) return
        ref.current.style.transition = 'transform 0.5s cubic-bezier(.2,.8,.2,1)'
        ref.current.style.transform = ''
      }}
    >
      {children}
    </div>
  )
}

/** Global cursor: dot follows with easing; elements with data-cursor="Label" swell into a labelled disc. */
export function Cursor() {
  const el = useRef<HTMLDivElement>(null)
  const [label, setLabel] = useState('')
  useEffect(() => {
    if (!window.matchMedia('(pointer: fine)').matches) return
    let tx = -100, ty = -100, x = -100, y = -100, raf = 0
    const move = (e: PointerEvent) => {
      tx = e.clientX
      ty = e.clientY
      const t = (e.target as HTMLElement | null)?.closest<HTMLElement>('[data-cursor]')
      setLabel(t?.dataset.cursor ?? '')
    }
    const tick = () => {
      x += (tx - x) * 0.22
      y += (ty - y) * 0.22
      if (el.current) el.current.style.transform = `translate(${x}px, ${y}px)`
      raf = requestAnimationFrame(tick)
    }
    window.addEventListener('pointermove', move)
    raf = requestAnimationFrame(tick)
    return () => {
      window.removeEventListener('pointermove', move)
      cancelAnimationFrame(raf)
    }
  }, [])
  return (
    <div ref={el} className={`cursor ${label ? 'has-label' : ''}`} aria-hidden>
      <span>{label}</span>
    </div>
  )
}

/** Risk tag. Shape + label + colour, so it never relies on colour alone. */
export function RiskTag({ risk, className = '' }: { risk: Risk; className?: string }) {
  const s: Record<Risk, string> = {
    high: 'bg-pen-d text-white border-pen-d',
    medium: 'bg-[#ffb020] text-ink border-ink',
    low: 'bg-transparent text-ink border-ink',
  }
  const g: Record<Risk, string> = { high: '▲', medium: '◆', low: '●' }
  return (
    <span className={`mono inline-flex items-center gap-1.5 border-2 px-2 py-0.5 font-bold ${s[risk]} ${className}`}>
      <span aria-hidden>{g[risk]}</span>
      {riskLabel[risk]}
    </span>
  )
}

export const riskBar: Record<Risk, string> = { high: '#c22a12', medium: '#ffb020', low: '#0f110e' }

/** Renders "**bold**" markers as highlighter swipes. */
export function Marked({ text }: { text: string }) {
  return (
    <>
      {text.split('**').map((part, i) => (i % 2 ? <mark key={i} className="hl">{part}</mark> : <span key={i}>{part}</span>))}
    </>
  )
}

/** Count-up number. */
export function CountUp({ to, ms = 900 }: { to: number; ms?: number }) {
  const [n, setN] = useState(0)
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setN(to)
      return
    }
    const t0 = performance.now()
    let raf = 0
    const step = (t: number) => {
      const p = Math.min(1, (t - t0) / ms)
      setN(Math.round(to * (1 - Math.pow(1 - p, 3))))
      if (p < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [to, ms])
  return <>{n}</>
}

export function NavLink2(props: LinkProps) {
  return <Link viewTransition {...props} />
}

export function Wordmark({ dark = false }: { dark?: boolean }) {
  return (
    <NavLink2 to="/" data-cursor="Home" className="inline-flex min-h-11 items-center gap-2 no-underline" style={{ color: dark ? '#f3f3ee' : '#0f110e' }}>
      <span className="relative inline-block h-6 w-6 border-2" style={{ borderColor: 'currentColor' }} aria-hidden>
        <span className="absolute inset-x-0 top-[7px] h-[7px] bg-lime" />
      </span>
      <span className="display text-[22px]" style={{ letterSpacing: '-0.04em' }}>Fineprint</span>
    </NavLink2>
  )
}
