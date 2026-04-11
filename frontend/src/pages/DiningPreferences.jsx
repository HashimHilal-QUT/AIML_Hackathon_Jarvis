import { Link } from 'react-router-dom'
import { MaterialIcon } from '../components/MaterialIcon'
import {
  cuisineLabelToId,
  usePreferences,
  WELCOME_CUISINE_LABELS,
  WELCOME_DIETARY_LABELS,
} from '../context/PreferencesContext'

/** Stitch / Discover 由来の Google Aida 画像 */
const IMG_PIZZA =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuAwpOXKiZrg50xGbU8GBKxKPvQ0vPcJpTmnkAzNZDRf2sSE8LqZOkTENFDXcCzHvgvMIYh27qdKh6EfFWGO_WNElKjmN7w226_hkplQR5U361XCXFtVHBaXM-tEjNZ0ZyW26F4OThwxBjbHIaMb0DzHc1FvmSU0girlyJIsZYb8DvG4aJYkTx20cbYhnmMpd3aASDl7nGqy5Xxb3cG80kz3jmOFh_1akMgDRJIE1nuoLqGmWNNMcrBaGUkK8kzwsAp5Bb8YY21JluRV'
const IMG_SUSHI =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuDn2wqkNCBmJ622nfkSZE2u_SRvbCx9oB6mzdroSdw427_T8LU-R6KNYenoG_xWFrU83dMoqrCJGwK6CFi6248Gz629213_EFnFSU1T-q8L7MDfek4c1b8u4vj9s7oBKD92FfeN3_emO-xa7OSFxFYor8wgJ_jQLwMx1bFX7UcTAdXrQT0pRb-8GZ4pKfWY5si51939AZnS_ufva8sy8z_7gLXmpalTwywzfglUzEw_rRTYz2FdsTsM6tsDwxa4l-OyPelNMnyvT9NR'
const IMG_GREEK_SALAD =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuCy6JLhGXi59WghFbZyvdGS3g2lMWmrFN35QfNf4Sm83P56ZKd0aZRZXLriQzpDnnqIKXw-hLBkHz6TASN_fDj4oEPXu14xrNKS1HlzuQjb_ZeiDX9PvOS_QIfQxdBkoKK8CX2DwHHAOCFsrnSf0IuilrJLBCw6ZIrfbNMv-4jxV5awJ4tsaRcZGB0VMh6NIWG8Ct0GZC6uX0PBve1cfwp3mIuXqG8AW6nTkrpQLOCjn3qgFeWYN3cThSLmUucSAD3Xlt9yWGfFRsY'
const IMG_CURRY =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuA6vzRTiTfl9UI_zbaqcAtZEfe2v5Gd3INUktIj_SY3mwqM-Jj-JnbURjoPOHFyfLAh3IBiRyZn_yWlUm6VmKSL5SRkQz4robBaW7_EUD50tTd16AJ7VnRpQdp2swj8gRgrcJVq-OqPodltJqv17lnIW-wedCkIVqrbgtKJkrHPhreRla3sHlYejlNnG4hn07UyGa7Whxs_LfnJVFiLD1cp0_NCpTP2VOpWE5axnQtiMGvjyKENzaDYhqBy_MOToQmPrcQ6M9glHhk'

/** リポジトリに無い地域向けは Unsplash（料理の内容が分かるもの） */
const IMG_TACOS =
  'https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
const IMG_THAI =
  'https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=800&q=80'
const IMG_KOREAN =
  'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
const IMG_PHO =
  'https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=800&q=80'

/** Welcome と同じ8種。各国・地域に合わせた画像 */
const CUISINE_IMAGES = {
  italian: IMG_PIZZA,
  japanese: IMG_SUSHI,
  mexican: IMG_TACOS,
  indian: IMG_CURRY,
  mediterranean: IMG_GREEK_SALAD,
  thai: IMG_THAI,
  korean: IMG_KOREAN,
  vietnamese: IMG_PHO,
}

const CUISINES = WELCOME_CUISINE_LABELS.map((label) => {
  const id = cuisineLabelToId(label)
  return { id, label, img: CUISINE_IMAGES[id] }
})

export default function DiningPreferences() {
  const {
    diningCuisineIds,
    budgetAmount,
    budgetTier,
    dietaryKeys,
    toggleDiningCuisine,
    setBudgetAmount,
    setBudgetTier,
    toggleDietary,
  } = usePreferences()

  const selected = new Set(diningCuisineIds)
  const diet = new Set(dietaryKeys)

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
                  onClick={() => toggleDiningCuisine(c.id)}
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
                  value={budgetAmount}
                  onChange={(e) => setBudgetAmount(Number(e.target.value))}
                  aria-valuemin={10}
                  aria-valuemax={100}
                  aria-valuenow={budgetAmount}
                  aria-label="Daily budget in dollars"
                />
                <div className="flex justify-between mt-4 text-sm font-semibold text-on-surface-variant">
                  <span>$10</span>
                  <span className="text-primary bg-primary-container/20 px-3 py-1 rounded-full">
                    ${budgetAmount}
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
              {WELCOME_DIETARY_LABELS.map((label) => {
                const key = label.toLowerCase().replace(/\s+/g, '-')
                const on = diet.has(key)
                return (
                  <button
                    key={label}
                    type="button"
                    onClick={() => toggleDietary(key)}
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
