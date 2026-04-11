import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MaterialIcon } from '../components/MaterialIcon'

const CUISINES = [
  {
    id: 'asian',
    label: 'Asian',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA_-pre3P7aFJytrw-p9pXBlAtck2NSgXwRWC-rixDj0-Hl0vaaEwQ3cHNH3G9UBIbzU9HXTbYRL9kcbfgIOPZft8dVNx4kOwwhdbEg6jRSMwd47Ke8yk9Rucex2dxYTMzRq_741nXLT4dfUMZ-4eAimgIQzDiJ4-ee_BJv6P4b1ZlIwVQW8snvtkDi1w9MyQbsH4sF2k5EilChbvwgvNRk-AUbbF61hxWn4PJlpNcxOa0Q3BiYZ7NWdP5ahthFQQIUUUl1bMdmwo0',
  },
  {
    id: 'western',
    label: 'Western',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCLFJPYuqu4--2_dZkEIaVHhCNQ9bByKMkh3vNvZoMbDSIpj5eu-WvECdsoYfCbL7eh8fZ39Sd7kAF8eVsHzGgNe1Nv6d18hfEAqydILQyXfqXzGVrQAPoXNeMYMu3wyWFfiEQ-GzZ8tdbGHHFH0HfqEZTtRScMiNRTRtz67Qsa4o8LIAfeq1l71xcMbjm8OlTclc7pruGbm8rkqDJ68XT75GrC9azClQkvhYNilYfcfCJKXLHdYiSebrsIDluoOGf2ZsjJtDtK_t4',
  },
  {
    id: 'italian',
    label: 'Italian',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCy6JLhGXi59WghFbZyvdGS3g2lMWmrFN35QfNf4Sm83P56ZKd0aZRZXLriQzpDnnqIKXw-hLBkHz6TASN_fDj4oEPXu14xrNKS1HlzuQjb_ZeiDX9PvOS_QIfQxdBkoKK8CX2DwHHAOCFsrnSf0IuilrJLBCw6ZIrfbNMv-4jxV5awJ4tsaRcZGB0VMh6NIWG8Ct0GZC6uX0PBve1cfwp3mIuXqG8AW6nTkrpQLOCjn3qgFeWYN3cThSLmUucSAD3Xlt9yWGfFRsY',
  },
  {
    id: 'indian',
    label: 'Indian',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA6vzRTiTfl9UI_zbaqcAtZEfe2v5Gd3INUktIj_SY3mwqM-Jj-JnbURjoPOHFyfLAh3IBiRyZn_yWlUm6VmKSL5SRkQz4robBaW7_EUD50tTd16AJ7VnRpQdp2swj8gRgrcJVq-OqPodltJqv17lnIW-wedCkIVqrbgtKJkrHPhreRla3sHlYejlNnG4hn07UyGa7Whxs_LfnJVFiLD1cp0_NCpTP2VOpWE5axnQtiMGvjyKENzaDYhqBy_MOToQmPrcQ6M9glHhk',
  },
  {
    id: 'healthy',
    label: 'Healthy',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDpZcIXDzN3vS8NW4e2cPeY_MpqiNM9lugKkXBoN_cRzh-KVj0_dqXdAo7oA0BQfx4b1NFbyTcE5xAdPjWbczDawNezaYzY52GZg3giGlKaAIWlJauScp0WxK7svKuaud2m7TqcTihd_NbyEU-VgLs3kjVtCI5hKQSTIvgI2cn4qe1mEEi48N7uNI5vsXFysv_ywVcI3CH-1QNQ5nnFwRwZkDApfsBKCCIrLlrXIqH7wTJ7sCmONoqbHiJ6L7MDeikwLnty7P8omaQ',
  },
]

const DIETARY = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Halal', 'Dairy-Free', 'Nut Allergy', 'Low Carb']

export default function DiningPreferences() {
  const [selected, setSelected] = useState(() => new Set(['asian', 'healthy']))
  const [budgetTier, setBudgetTier] = useState('value')
  const [diet, setDiet] = useState(() => new Set(['vegetarian', 'halal']))
  const [budget, setBudget] = useState(30)

  const toggleCuisine = (id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleDiet = (key) => {
    setDiet((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  return (
    <main className="max-w-4xl mx-auto px-6 pt-12 pb-24 md:pt-20 bg-surface font-body text-on-surface antialiased min-h-screen">
      <header className="mb-12 text-center md:text-left">
        <span className="text-secondary font-bold tracking-widest uppercase text-xs mb-4 block">
          Step 2 of 4
        </span>
        <h1 className="font-headline font-extrabold text-4xl md:text-5xl text-on-surface mb-4 leading-tight">
          Tell us what you <span className="text-secondary">crave</span>.
        </h1>
        <p className="text-on-surface-variant text-lg max-w-xl">
          Personalize your Meal Buddy experience. We&apos;ll use these to find your perfect culinary
          matches.
        </p>
      </header>

      <form
        className="space-y-16"
        onSubmit={(e) => {
          e.preventDefault()
        }}
      >
        <section>
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-headline font-bold text-2xl">Cuisine Preferences</h2>
            <span className="text-primary font-semibold text-sm">Select multiple</span>
          </div>
          <div
            className="grid gap-4"
            style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))' }}
          >
            {CUISINES.map((c) => {
              const on = selected.has(c.id)
              return (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => toggleCuisine(c.id)}
                  className={`cuisine-card text-left overflow-hidden rounded-[2rem] bg-surface-container-low transition-all duration-300 shadow-sm h-48 flex flex-col border-4 ${
                    on ? 'border-secondary bg-white' : 'border-transparent'
                  }`}
                >
                  <div className="h-32 w-full overflow-hidden">
                    <img className="cuisine-img w-full h-full object-cover transition-transform duration-500" alt="" src={c.img} />
                  </div>
                  <div className="p-3 flex items-center justify-between mt-auto">
                    <span className="font-headline font-bold text-sm uppercase tracking-wide">{c.label}</span>
                    {on ? <MaterialIcon name="check_circle" className="text-secondary" /> : null}
                  </div>
                </button>
              )
            })}
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-surface-container-low rounded-[2rem] p-8">
            <div className="flex items-center gap-3 mb-6">
              <MaterialIcon name="payments" className="text-primary text-3xl" />
              <h2 className="font-headline font-bold text-xl">Daily Budget Range</h2>
            </div>
            <div className="space-y-8">
              <div className="relative pt-4">
                <input
                  className="w-full h-2 bg-surface-container-highest rounded-lg appearance-none cursor-pointer accent-primary"
                  max={100}
                  min={10}
                  type="range"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                />
                <div className="flex justify-between mt-4 text-sm font-semibold text-on-surface-variant">
                  <span>$10</span>
                  <span className="text-primary bg-primary-container/20 px-3 py-1 rounded-full">
                    $30 - $45
                  </span>
                  <span>$100+</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { id: 'budget', label: '$ (Budget)' },
                  { id: 'value', label: '$$ (Value)' },
                  { id: 'premium', label: '$$$ (Premium)' },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setBudgetTier(t.id)}
                    className={`py-3 px-4 rounded-[2rem] border-2 text-sm font-bold transition-all ${
                      budgetTier === t.id
                        ? 'bg-primary text-on-primary border-primary'
                        : 'bg-surface-container-lowest text-on-surface border-transparent hover:border-primary-container'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="md:col-span-3 bg-white rounded-[2rem] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <MaterialIcon name="info" className="text-tertiary text-3xl" />
              <h2 className="font-headline font-bold text-xl">Dietary Requirements &amp; Allergies</h2>
            </div>
            <div className="flex flex-wrap gap-3">
              {DIETARY.map((label) => {
                const key = label.toLowerCase().replace(/\s+/g, '-')
                const on = diet.has(key)
                return (
                  <button
                    key={label}
                    type="button"
                    onClick={() => toggleDiet(key)}
                    className={
                      on
                        ? 'bg-tertiary-container text-on-tertiary-container px-6 py-3 rounded-full font-bold text-sm flex items-center gap-2 hover:bg-tertiary-fixed transition-colors'
                        : 'bg-surface-container-high text-on-surface-variant px-6 py-3 rounded-full font-bold text-sm flex items-center gap-2 hover:bg-surface-container-highest transition-colors'
                    }
                  >
                    {on && label === 'Vegetarian' ? (
                      <MaterialIcon name="eco" className="text-lg" filled />
                    ) : null}
                    {on && label === 'Halal' ? (
                      <MaterialIcon name="verified" className="text-lg" filled />
                    ) : null}
                    {label}
                  </button>
                )
              })}
              <button
                type="button"
                className="bg-surface-container-low border-2 border-dashed border-outline-variant text-outline px-6 py-3 rounded-full font-bold text-sm flex items-center gap-2 hover:bg-white transition-colors"
              >
                <MaterialIcon name="add" className="text-lg" />
                Add Custom
              </button>
            </div>
          </div>
        </section>

        <footer className="mt-20 flex flex-col md:flex-row items-center justify-between gap-6">
          <Link
            to="/welcome"
            className="text-on-surface-variant font-bold hover:text-primary transition-colors flex items-center gap-2 order-2 md:order-1"
          >
            <MaterialIcon name="arrow_back" />
            Back
          </Link>
          <div className="flex items-center gap-4 w-full md:w-auto order-1 md:order-2">
            <Link
              to="/discover"
              className="w-full md:w-64 bg-secondary text-on-secondary py-4 px-8 rounded-2xl font-headline font-extrabold text-lg shadow-xl shadow-secondary/20 hover:bg-secondary-dim transition-all active:scale-95 text-center inline-block"
            >
              Finish Setup
            </Link>
          </div>
        </footer>
      </form>
    </main>
  )
}
