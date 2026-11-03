import { useEffect } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import { Cursor } from './components/ui'
import Home from './pages/Home'
import Reading from './pages/Reading'
import ContractLayout from './pages/ContractLayout'
import Overview from './pages/Overview'
import Review from './pages/Review'
import Negotiate from './pages/Negotiate'

function ScrollTop() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (!hash) {
      window.scrollTo(0, 0)
      return
    }
    // the target mounts after the first render, so wait a tick before scrolling to it
    const t = setTimeout(() => document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: 'smooth' }), 80)
    return () => clearTimeout(t)
  }, [pathname, hash])
  return null
}

function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center bg-ink p-8 text-paper">
      <div>
        <p className="mono text-pen">▲ Lost</p>
        <h1 className="display mt-3 text-[clamp(48px,9vw,140px)]">Page not <mark className="hl in">found</mark></h1>
        <Link to="/" className="btn mt-8 no-underline">← Back home</Link>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <>
      <ScrollTop />
      <Cursor />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/c/:id/reading" element={<Reading />} />
        <Route path="/c/:id" element={<ContractLayout />}>
          <Route index element={<Overview />} />
          <Route path="review" element={<Review />} />
          <Route path="negotiate" element={<Negotiate />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  )
}
