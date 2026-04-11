import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { MaterialIcon } from '../components/MaterialIcon'

const MAX_PICKS = 3

const HOT = [
  {
    id: 'hot-grill-chill',
    rank: 'No 1',
    rankClass: 'bg-secondary text-on-secondary',
    title: 'Grill & Chill',
    sub: 'Best Artisanal Burgers in Town',
    rating: '4.9 ★',
    tag: 'Social Favorite',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDrXXjD4yYo8nwSjGnnAaZS_CJCBaHxEmDhp1Q8xhXiW05UwSw1r7fZsK7Ow7iMkx4RSk2agaQ23zmVdBLiF8ntUQsGuoxu1WxGJ_qGSC1vsaudq7GbBWsQcjUp-qTaKRsvAUClygYvzeNZTiReoWA4ZTldnjzDZRT7FlFKlt2DKlkyMlCbY5K91RZbDEW5DZ67sw5UraDDJRR4OgijNl02_x0tcxrG9g1KqzbhHOOXKbyyIHt4snp4AzOAO7pl1YPZbFTyDxRHsiTd',
  },
  {
    id: 'hot-sushi-zen',
    rank: 'No 2',
    rankClass: 'bg-primary text-on-primary',
    title: 'Sushi Zen',
    sub: 'Authentic Japanese Experience',
    rating: '4.8 ★',
    tag: 'Most Shared',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDn2wqkNCBmJ622nfkSZE2u_SRvbCx9oB6mzdroSdw427_T8LU-R6KNYenoG_xWFrU83dMoqrCJGwK6CFi6248Gz629213_EFnFSU1T-q8L7MDfek4c1b8u4vj9s7oBKD92FfeN3_emO-xa7OSFxFYor8wgJ_jQLwMx1bFX7UcTAdXrQT0pRb-8GZ4pKfWY5si51939AZnS_ufva8sy8z_7gLXmpalTwywzfglUzEw_rRTYz2FdsTsM6tsDwxa4l-OyPelNMnyvT9NR',
  },
  {
    id: 'hot-rustic-pizza',
    rank: 'No 3',
    rankClass: 'bg-tertiary text-on-tertiary',
    title: 'Rustic Pizza',
    sub: 'Traditional Wood-Fired Slices',
    rating: '4.7 ★',
    tag: 'Top Rated',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAyrsWZI8z8iRwLraxnhL97PPaInk3S52stol6sxEchNuEi5WpkZ5arCmoFd9LOkYLUNuNFU6YCLlEIU58zgw5uSSpPZVH4IQ6FxIGgwbZDGtrfV8bcX0G1xjmxA8hu5s-b-fvlVujg1eXeEP0Td1SDEyw8_4gGefi25-BwSUz4N1AmbtaKpzBiUr_-JxQbvK2xdctJ-1INgcEpg3cnJ1WpPUcMGNTTyDFeHb71cZutZP9BL7AVnyZL2pEuYOxGufX2jpvXCVnJvCni',
  },
]

const AV =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuB1-TRZGGJQbC_OmR9XwEhdIoLtJCETjgtOQGIgef_t1yTWLb5HlrMkV1OI8-0UV2BUjV4RRcJL3S8FTdB2_y8CmslMWNukJS3MkHBvKOgYj5Yy_MpLCK5xm-dva6YXhUa6QVVGYhrwthvIKSwjMyB_HcnoM_tMBxvCl4FHL-lx2JI-TWEzdXE7YatZuYc8c1wr1XecW5duQ_T3m7lcVc_k1d4wCVMY6TN5t-Zjtr_yHrDV526LG_NG_FPOXaeOJtkHsW7FbPO-mQfV'

/** 最初に9件表示。View more で残りを表示 */
const CURATED_ALL = [
  {
    id: 'cur-pancake-palace',
    name: 'Pancake Palace',
    blurb: '"The best breakfast in the city"',
    price: '$12-$20',
    social: '12 Friends Ate Here',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAbS85he-vL6qoaMjlZsqPGJ56NI1vKBbIf8ij-Xj2x-LFfGNPGw0lnwWV2peDzAiKUrGmVZ7Ae8_y62LE3dvtiYvGOi0YJs_MozS2cLgaScqYVGZmJJUmnCO9P-pSdVsMX6rF6aT0Fj3ulnkeg0x302rX1oGLeadSC8YObF1mqSzj3Z19TMs0xNsgcAliya87abjm6fbA-pK8w3BvJjDDpaLPxkyR4RFthvpVSnFtH2ywaJRHUCimKfH_y_lOwkaicCJSsCeTKj_vv',
    avatars: [AV, 'https://lh3.googleusercontent.com/aida-public/AB6AXuAZ0uPjOa0GAevqlGq0ipjHML77MnK2teBF8uqaeQsi4YSHshXp86VKT51VOSfEEICWRLX3K6SEywIruBwSefvctOqWDQogSJKN79yv6vPS2urpfM6MHjEuv5VT6Pu6VwwE1yp7Z97EBAUcSirThgi0KSMiS2gH9J_4jkMncKuaWyK-RDOeSwcw0r98GycpNU1KHJLSPUYX_a64GHYBpyRarXjYOeBTI8EAz-nC4_vvQm6xNxBglWn0VJf_nsT0Xn6oVc9eYi9AZ7AW'],
  },
  {
    id: 'cur-glass-house',
    name: 'The Glass House',
    blurb: '"Elegant dining, refined taste"',
    price: '$40-$80',
    social: '5 Matches Today',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDfrPCbLUljQrPrXybPlgSn3w-Ioqy8YoXqau1POeemL6ZNOy3XaZpHcbezemlMDP7wc7Z8a7dVzbLmJ9K5dR-itpyiy1elCHCo0n2rtfcCo15NSIW_HApY2jQezZrXC-w0mMXtfI970utxIIugIxZpDnPs0evhDTc0o6wmG5cg-QjO7GpfJ8VJNZJI0OjlruWvk2fSxHKI2883LulQEW3lcgJb3M9W6Ey_mkSpujEm7-J8f_projHDWjrr39MidHLgHlnxuC_P5dOT',
    avatars: [
      'https://lh3.googleusercontent.com/aida-public/AB6AXuDZXrQw69xCx4Y9A6pQWV3ZxdNp8_DIYSpnDqlNFp-Sxhv_MFtiyWAUuURlKlWipJTAf8AD4buYXXt6dkc3-PFf_Dqy-gcO-eAOWjHxTNuLRKhnBhN6MOKAOJQvDSgM0By2J74DbdvwjgMU2DUrYRvIqpnoAf9YGRlNfYsYBn0m-dLjkCWSYKRB56hr7DT3eQ3yg2YhhXK73Iylw5nLlU86jl3j9PRToCvz85uneLPERLmthctJ3iFGDuBpI7_H26ECzznO6hPCvsx1',
    ],
  },
  {
    id: 'cur-napoli-slices',
    name: 'Napoli Slices',
    blurb: '"A slice of Italy in every bite"',
    price: '$15-$25',
    social: '8 Friends Interested',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAwpOXKiZrg50xGbU8GBKxKPvQ0vPcJpTmnkAzNZDRf2sSE8LqZOkTENFDXcCzHvgvMIYh27qdKh6EfFWGO_WNElKjmN7w226_hkplQR5U361XCXFtVHBaXM-tEjNZ0ZyW26F4OThwxBjbHIaMb0DzHc1FvmSU0girlyJIsZYb8DvG4aJYkTx20cbYhnmMpd3aASDl7nGqy5Xxb3cG80kz3jmOFh_1akMgDRJIE1nuoLqGmWNNMcrBaGUkK8kzwsAp5Bb8YY21JluRV',
    avatars: [
      'https://lh3.googleusercontent.com/aida-public/AB6AXuB6N98sYLbNafW9E3JiIVP8YP_eL4MEWYNUVeQj4rEJmj1lKAwCtByZUwirwDbk2H07PsAuGpIcHSS4c9T93lyITYMqqcSWHNSGD6B9T-_eguc5F61lwh5M_42Xt5a-UhEgyE69sDW0uvDrJgpeS8fvplJcHL1cMsiqArGEFvbcZtQQcQYWMn2uxNdN1-1PJ4RhzL2y4J5HrI8tvdlTjjNNc3I5-MJwDxOsRCcE9CtL6kCaiXzQdWk8F9eVTmCq7umGd6MyS6oM2n4t',
      'https://lh3.googleusercontent.com/aida-public/AB6AXuClHKFQienWtBlQakJHstzeYnIaOpj1XxvG5IBGXG-rFsfrGoE1SWxdiILc0CSWDfDmp9_3RxIHBiQ3vZ75XY0uoSNylxbrq03gUx_7PjM3mS_Y-SSoC1gHP1YzTDB8rLliJCDkRoYFP6tm9evd4gj2sVMjBwcOjPYfdxA9vUhbvfl8GvOWcPpdSe0Tbj5gdd9rmJIre1e4OVDrGbDxwy677kNbtrxq_-sczlLzHapUKeKtuSrTqvjmIbYn9q3T20EoHUqs2cWlEkTe',
      'https://lh3.googleusercontent.com/aida-public/AB6AXuCBToqsytOU6Byb6icd0dpWmubnmPIDaR3T2Zth8iwiJdnoZU-uLOZ1fKG1N2PNlB_d6-WKAV2sMgH03SE0WwZvZcBg1AsYxO9_4LcUiFOagrpJvkiQlcJOJZhPMY22kH9CmW5jHSLpsQQvsEj3ONCsFKPsgHBRMS4ExYRCiV62JtgUQg1KVySXS1ak_dn5Ed9czZ6px60VqOmc3N-fvX_b3373n8jV1y4q9hCuTZZX1UyhJOS7F5J5Vgu1MybZd2_DjwFkov12IvB0',
    ],
  },
  {
    id: 'cur-taco-fiesta',
    name: 'Taco Fiesta',
    blurb: '"Fresh street-style tacos daily"',
    price: '$8-$16',
    social: '9 Friends Ate Here',
    img: 'https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
    avatars: [AV],
  },
  {
    id: 'cur-seoul-bbq',
    name: 'Seoul BBQ House',
    blurb: '"Korean BBQ done right"',
    price: '$22-$38',
    social: '6 Matches This Week',
    img: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
    avatars: [AV, AV],
  },
  {
    id: 'cur-bangkok-bowl',
    name: 'Bangkok Bowl',
    blurb: '"Bold Thai flavors, fast lunch"',
    price: '$11-$18',
    social: '14 Friends Interested',
    img: 'https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=800&q=80',
    avatars: [AV],
  },
  {
    id: 'cur-saigon-pho',
    name: 'Little Saigon Pho',
    blurb: '"Steam rising, broth for days"',
    price: '$10-$17',
    social: '7 Friends Ate Here',
    img: 'https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=800&q=80',
    avatars: [AV, AV],
  },
  {
    id: 'cur-green-garden',
    name: 'Green Garden Cafe',
    blurb: '"Bowls, smoothies, good vibes"',
    price: '$9-$15',
    social: '11 Friends Interested',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCkpjxXYbzRHIfmTXAAWgUrSsmNcu24q9y4Ibn3WYZPFX_SJxKjEKFkPmB2TCJlMWXnSbSyr_73f868VBZh41boSWaznwuZ8sgEpdvKzDjpUPb2EE2fsupSthvP7P1QqVdAtGKyWHvSq_C70q9_78MWejDYhYFqSoA3NVpfhtyZM8l1fXu334hH4FBe7K2ZQxKT31P4-uxvElq_ouA6WnwdMVZTjoQqMxredSUWMWbw1R_Dcqc7LbIMO5HfVfZzQA-LFas3fNv5dfBr',
    avatars: [AV],
  },
  {
    id: 'cur-urban-burger',
    name: 'Urban Burger Co.',
    blurb: '"Smash patties & secret sauce"',
    price: '$14-$22',
    social: '20 Friends Ate Here',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDrXXjD4yYo8nwSjGnnAaZS_CJCBaHxEmDhp1Q8xhXiW05UwSw1r7fZsK7Ow7iMkx4RSk2agaQ23zmVdBLiF8ntUQsGuoxu1WxGJ_qGSC1vsaudq7GbBWsQcjUp-qTaKRsvAUClygYvzeNZTiReoWA4ZTldnjzDZRT7FlFKlt2DKlkyMlCbY5K91RZbDEW5DZ67sw5UraDDJRR4OgijNl02_x0tcxrG9g1KqzbhHOOXKbyyIHt4snp4AzOAO7pl1YPZbFTyDxRHsiTd',
    avatars: [AV, AV, AV],
  },
  {
    id: 'cur-matcha-lab',
    name: 'Matcha Lab',
    blurb: '"Desserts & specialty drinks"',
    price: '$6-$12',
    social: '4 Matches Today',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAbS85he-vL6qoaMjlZsqPGJ56NI1vKBbIf8ij-Xj2x-LFfGNPGw0lnwWV2peDzAiKUrGmVZ7Ae8_y62LE3dvtiYvGOi0YJs_MozS2cLgaScqYVGZmJJUmnCO9P-pSdVsMX6rF6aT0Fj3ulnkeg0x302rX1oGLeadSC8YObF1mqSzj3Z19TMs0xNsgcAliya87abjm6fbA-pK8w3BvJjDDpaLPxkyR4RFthvpVSnFtH2ywaJRHUCimKfH_y_lOwkaicCJSsCeTKj_vv',
    avatars: [AV],
  },
  {
    id: 'cur-harbor-fish',
    name: 'Harbor Fish Grill',
    blurb: '"Catch of the day, always"',
    price: '$18-$32',
    social: '8 Friends Ate Here',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDn2wqkNCBmJ622nfkSZE2u_SRvbCx9oB6mzdroSdw427_T8LU-R6KNYenoG_xWFrU83dMoqrCJGwK6CFi6248Gz629213_EFnFSU1T-q8L7MDfek4c1b8u4vj9s7oBKD92FfeN3_emO-xa7OSFxFYor8wgJ_jQLwMx1bFX7UcTAdXrQT0pRb-8GZ4pKfWY5si51939AZnS_ufva8sy8z_7gLXmpalTwywzfglUzEw_rRTYz2FdsTsM6tsDwxa4l-OyPelNMnyvT9NR',
    avatars: [AV, AV],
  },
  {
    id: 'cur-campus-coffee',
    name: 'Campus Coffee Roasters',
    blurb: '"Third-wave espresso & pastries"',
    price: '$4-$11',
    social: '25 Friends Interested',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDfrPCbLUljQrPrXybPlgSn3w-Ioqy8YoXqau1POeemL6ZNOy3XaZpHcbezemlMDP7wc7Z8a7dVzbLmJ9K5dR-itpyiy1elCHCo0n2rtfcCo15NSIW_HApY2jQezZrXC-w0mMXtfI970utxIIugIxZpDnPs0evhDTc0o6wmG5cg-QjO7GpfJ8VJNZJI0OjlruWvk2fSxHKI2883LulQEW3lcgJb3M9W6Ey_mkSpujEm7-J8f_projHDWjrr39MidHLgHlnxuC_P5dOT',
    avatars: [AV],
  },
]

const CURATED_INITIAL = 9

function NavItem({ to, icon, label, end }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex flex-col items-center justify-center rounded-full px-6 py-2 transition-transform duration-300 ease-out ${
          isActive
            ? 'bg-blue-100 text-blue-800 scale-110'
            : 'text-slate-400 px-6 py-2 hover:text-blue-600'
        }`
      }
    >
      <MaterialIcon name={icon} />
      <span className="font-headline text-[10px] font-bold uppercase tracking-wider mt-1">{label}</span>
    </NavLink>
  )
}

function PickToggleButton({ selected, atMax, onClick }) {
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
      disabled={!selected && atMax}
      title={selected ? 'Remove from picks' : atMax ? `Maximum ${MAX_PICKS} restaurants` : 'Add to picks'}
      className={`absolute top-3 right-3 z-20 p-2 rounded-full transition-all ${
        selected
          ? 'bg-secondary text-on-secondary shadow-md'
          : atMax
            ? 'bg-white/10 text-white/40 cursor-not-allowed'
            : 'bg-white/20 backdrop-blur-md text-white hover:bg-white hover:text-primary'
      }`}
    >
      <MaterialIcon name={selected ? 'check' : 'add'} className="text-xl" />
    </button>
  )
}

export default function Discover() {
  const navigate = useNavigate()
  const [selectedIds, setSelectedIds] = useState(() => new Set())
  const [curatedExpanded, setCuratedExpanded] = useState(false)

  const count = selectedIds.size
  const atMax = count >= MAX_PICKS
  const canFindMatches = count >= 1

  const togglePick = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else if (next.size < MAX_PICKS) next.add(id)
      return next
    })
  }

  const curatedVisible = curatedExpanded ? CURATED_ALL : CURATED_ALL.slice(0, CURATED_INITIAL)
  const hasMoreCurated = CURATED_ALL.length > CURATED_INITIAL

  return (
    <div className="bg-surface text-on-surface pb-32 min-h-screen">
      <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-xl">
        <div className="flex justify-between items-center px-6 py-4 w-full max-w-7xl mx-auto gap-4">
          <Link to="/discover" className="text-2xl font-extrabold tracking-tight text-blue-700 shrink-0 font-headline">
            Meal Buddy
          </Link>
          <div className="flex items-center gap-4 flex-1 justify-end">
            <div className="hidden md:flex items-center bg-surface-container-high px-4 py-2 rounded-full max-w-md flex-1">
              <MaterialIcon name="search" className="text-on-surface-variant text-xl shrink-0" />
              <input
                className="bg-transparent border-none focus:ring-0 text-sm ml-2 w-full min-w-0 outline-none"
                placeholder="Search eateries..."
                type="search"
              />
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                className="p-2 hover:bg-slate-100 rounded-full transition-colors active:scale-90"
              >
                <MaterialIcon name="notifications" className="text-slate-500" />
              </button>
              <Link
                to="/dining-preferences"
                className="p-2 hover:bg-slate-100 rounded-full transition-colors active:scale-90"
                aria-label="Dining preferences"
              >
                <MaterialIcon name="account_circle" className="text-slate-500" />
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="pt-24 px-6 max-w-7xl mx-auto space-y-12">
        <section>
          <div className="flex justify-between items-end mb-6">
            <div>
              <span className="text-secondary font-bold tracking-widest uppercase text-xs">Trending Now</span>
              <h2 className="text-4xl font-extrabold tracking-tight mt-1 font-headline">The Hot List</h2>
            </div>
            <button type="button" className="text-primary font-bold text-sm hover:underline">
              View All
            </button>
          </div>
          <div className="flex overflow-x-auto gap-6 no-scrollbar pb-4 -mx-6 px-6">
            {HOT.map((item) => {
              const picked = selectedIds.has(item.id)
              return (
                <div
                  key={item.id}
                  className="relative shrink-0 w-80 group transition-transform duration-300 hover:scale-[1.02]"
                >
                  <div
                    className={`absolute -top-4 -left-4 z-10 px-4 py-2 rounded-[2rem] font-black text-2xl rotate-[-12deg] shadow-lg ${item.rankClass}`}
                  >
                    {item.rank}
                  </div>
                  <div className="h-96 rounded-[2rem] overflow-hidden bg-surface-container-low relative">
                    <img className="w-full h-full object-cover" alt="" src={item.img} />
                    <PickToggleButton
                      selected={picked}
                      atMax={atMax}
                      onClick={() => togglePick(item.id)}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex flex-col justify-end p-6 pointer-events-none">
                      <h3 className="text-white text-2xl font-bold font-headline">{item.title}</h3>
                      <p className="text-white/80 text-sm">{item.sub}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="bg-tertiary-container text-on-tertiary-container px-2 py-0.5 rounded text-[10px] font-bold uppercase">
                          {item.rating}
                        </span>
                        <span className="text-white/60 text-[10px] uppercase font-bold tracking-wider">
                          {item.tag}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        <section className="bg-surface-container-low -mx-6 px-6 py-12 rounded-[2.5rem]">
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight font-headline">Curated for you</h2>
              <p className="text-on-surface-variant mt-2 max-w-md">
                Pick up to {MAX_PICKS} restaurants you&apos;re craving to find your perfect dining match.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <div className="bg-surface-container-highest px-6 py-3 rounded-full flex items-center gap-2">
                <MaterialIcon name="restaurant" className="text-primary text-xl" />
                <span className="font-bold text-on-surface">
                  Selected <span className="text-primary">{count}/{MAX_PICKS}</span>
                </span>
              </div>
              <button
                type="button"
                disabled={!canFindMatches}
                onClick={() => navigate('/availability')}
                className={`px-8 py-3 rounded-2xl font-bold transition-all ${
                  canFindMatches
                    ? 'bg-primary text-on-primary shadow-lg shadow-primary/20 hover:bg-primary-dim cursor-pointer active:scale-[0.98]'
                    : 'bg-slate-400 text-white/90 opacity-60 cursor-not-allowed'
                }`}
              >
                Find Matches
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {curatedVisible.map((c) => {
              const picked = selectedIds.has(c.id)
              return (
                <div
                  key={c.id}
                  className={`bg-surface-container-lowest p-4 rounded-[2rem] group transition-all hover:bg-white hover:shadow-xl ${
                    picked ? 'ring-2 ring-secondary ring-offset-2 ring-offset-surface-container-low' : ''
                  }`}
                >
                  <div className="relative h-48 rounded-[2rem] overflow-hidden mb-4">
                    <img className="w-full h-full object-cover" alt="" src={c.img} />
                    <PickToggleButton
                      selected={picked}
                      atMax={atMax}
                      onClick={() => togglePick(c.id)}
                    />
                  </div>
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <h4 className="font-bold text-lg font-headline">{c.name}</h4>
                      <p className="text-on-surface-variant text-sm italic">{c.blurb}</p>
                    </div>
                    <span className="text-secondary font-bold shrink-0">{c.price}</span>
                  </div>
                  <div className="flex items-center gap-3 mt-4">
                    <div className="flex -space-x-2">
                      {c.avatars.map((src, i) => (
                        <img
                          key={i}
                          alt=""
                          className="w-6 h-6 rounded-full border-2 border-surface-container-lowest object-cover"
                          src={src}
                        />
                      ))}
                    </div>
                    <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-tighter">
                      {c.social}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
          {hasMoreCurated ? (
            <div className="mt-8 flex justify-center">
              <button
                type="button"
                onClick={() => setCuratedExpanded((v) => !v)}
                className="text-primary font-bold text-sm hover:underline px-4 py-2 rounded-full border border-primary/30 hover:bg-primary/5 transition-colors"
              >
                {curatedExpanded ? 'Show less' : 'View more'}
              </button>
            </div>
          ) : null}
        </section>

        <section className="pb-12">
          <h2 className="text-2xl font-extrabold mb-6 font-headline">Meal Buddy Stats</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-primary text-on-primary p-6 rounded-[2rem] relative overflow-hidden group">
              <div className="relative z-10">
                <p className="text-xs uppercase font-bold opacity-80 tracking-widest mb-1">Matches Made</p>
                <h4 className="text-4xl font-black font-headline">124</h4>
              </div>
              <MaterialIcon
                name="handshake"
                className="absolute -right-4 -bottom-4 text-8xl opacity-10 rotate-12 transition-transform group-hover:scale-110"
              />
            </div>
            <div className="bg-secondary text-on-secondary p-6 rounded-[2rem] relative overflow-hidden group">
              <div className="relative z-10">
                <p className="text-xs uppercase font-bold opacity-80 tracking-widest mb-1">Points Earned</p>
                <h4 className="text-4xl font-black font-headline">2,450</h4>
              </div>
              <MaterialIcon
                name="stars"
                className="absolute -right-4 -bottom-4 text-8xl opacity-10 rotate-12 transition-transform group-hover:scale-110"
                filled
              />
            </div>
            <div className="bg-tertiary text-on-tertiary p-6 rounded-[2rem] relative overflow-hidden group">
              <div className="relative z-10">
                <p className="text-xs uppercase font-bold opacity-80 tracking-widest mb-1">Eateries Visited</p>
                <h4 className="text-4xl font-black font-headline">18</h4>
              </div>
              <MaterialIcon
                name="restaurant"
                className="absolute -right-4 -bottom-4 text-8xl opacity-10 rotate-12 transition-transform group-hover:scale-110"
              />
            </div>
            <div className="bg-surface-container-highest p-6 rounded-[2rem] relative overflow-hidden group">
              <div className="relative z-10">
                <p className="text-xs uppercase font-bold text-on-surface-variant tracking-widest mb-1">
                  Social Rank
                </p>
                <h4 className="text-4xl font-black text-on-surface font-headline">Top 5%</h4>
              </div>
              <MaterialIcon
                name="trending_up"
                className="absolute -right-4 -bottom-4 text-8xl opacity-10 rotate-12 text-on-surface transition-transform group-hover:scale-110"
              />
            </div>
          </div>
        </section>
      </main>

      <nav className="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 pb-6 pt-2 bg-white/80 backdrop-blur-xl shadow-[0_-12px_32px_rgba(31,45,81,0.06)] rounded-t-[32px] md:hidden">
        <NavItem to="/discover" icon="explore" label="Discover" end />
        <NavItem to="/availability" icon="calendar_today" label="Availability" />
        <NavItem to="/matches" icon="group" label="Matches" />
        <NavItem to="/welcome" icon="person" label="Profile" />
      </nav>
    </div>
  )
}
