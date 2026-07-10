import { Link } from 'react-router-dom'

const facets = [
  {
    title: 'Talk it through',
    body: 'Vent about your day, think out loud about a decision, or just say the thing you have not said out loud yet.',
  },
  {
    title: 'Notice the pattern',
    body: 'Log how you are feeling and watch the shape of it over weeks, not just the spike of a single bad day.',
  },
  {
    title: 'Write it down',
    body: 'Keep a journal that remembers what you told it — and hands you a better question the next time you open it.',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Nav */}
      <header className="max-w-5xl mx-auto w-full px-6 py-6 flex items-center justify-between">
        <span className="font-display text-lg tracking-tight text-ink-100">SafeSpace</span>
        <nav className="flex items-center gap-6">
          <Link to="/login" className="text-sm text-ink-400 hover:text-ink-100 transition-colors">
            Log in
          </Link>
          <Link
            to="/register"
            className="text-sm bg-lamp-500 text-dusk-950 px-4 py-2 rounded-full font-medium hover:bg-lamp-400 transition-colors"
          >
            Start for free
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <main className="flex-1 flex items-center">
        <div className="max-w-5xl mx-auto w-full px-6 py-20 grid md:grid-cols-2 gap-12 items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-lamp-500 mb-6">
              a space to think out loud
            </p>
            <h1 className="font-display text-5xl md:text-6xl leading-[1.05] text-ink-100 mb-6">
              Some thoughts need
              <br />
              <span className="italic text-lamp-400">somewhere to land</span>
              <span className="text-lamp-500">.</span>
            </h1>
            <p className="text-ink-300 text-lg leading-relaxed max-w-md mb-8">
              SafeSpace is a companion for venting, reflecting, and journaling — one that
              remembers what matters to you and notices how you have been feeling over time.
              Not a therapist. Just somewhere to think, at 1am or on your lunch break.
            </p>
            <div className="flex items-center gap-4">
              <Link
                to="/register"
                className="bg-lamp-500 text-dusk-950 px-6 py-3 rounded-full font-medium hover:bg-lamp-400 transition-colors"
              >
                Start talking
              </Link>
              <Link to="/login" className="text-ink-300 hover:text-ink-100 transition-colors text-sm">
                I already have an account →
              </Link>
            </div>
          </div>

          {/* Signature element: a slow-breathing presence orb — evokes a calm, attentive listener */}
          <div className="relative h-80 md:h-96 flex items-center justify-center" aria-hidden="true">
            <div className="absolute w-64 h-64 rounded-full bg-lamp-500/20 blur-3xl animate-breathe" />
            <div className="absolute w-40 h-40 rounded-full bg-lamp-400/30 blur-2xl animate-breathe [animation-delay:1.5s]" />
            <div className="relative w-28 h-28 rounded-full bg-gradient-to-br from-lamp-400 to-lamp-600 shadow-[0_0_60px_rgba(232,168,84,0.35)]" />
          </div>
        </div>
      </main>

      {/* Three facets — not numbered, since these aren't a sequence */}
      <section className="border-t border-dusk-700">
        <div className="max-w-5xl mx-auto px-6 py-16 grid md:grid-cols-3 gap-10">
          {facets.map((f) => (
            <div key={f.title}>
              <h3 className="font-display text-xl text-ink-100 mb-2">{f.title}</h3>
              <p className="text-ink-400 text-sm leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-dusk-700 py-8">
        <p className="text-center text-xs text-ink-400 font-mono">
          SafeSpace is not a substitute for professional mental health care.
        </p>
      </footer>
    </div>
  )
}
