import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { MaterialIcon } from '../components/MaterialIcon'

const PROFILE =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuCHfIX5N9uZQ4CL661nKVqWJpPhoZW1V_7uPvvQGmx2QyZmzjbuisR4Vri_QK0x-Ji9qGsLPnpiSuB02-89f-5TL2SzO7lM2ElSJUgRiMiNm74aUYWPUqXJNWQwbvu543_9vLvGyIgQzHykgS6TzzmQKlKNpFIiYYfH8h18nAXInpp_snPO-e16Zz9RylBs2cKRMh2nTB0lt7JndCjnXK_QAuN34rAyJ4wd4h8cDKmZSmDSXF4CEZyS-HXjF4B9vPQXtAo616r7ZRU'

const DAYS = [
  { label: 'Mon', date: '14', active: false },
  { label: 'Tue', date: '15', active: false },
  { label: 'Wed', date: '16', active: true },
  { label: 'Thu', date: '17', active: false },
  { label: 'Fri', date: '18', active: false },
  { label: 'Sat', date: '19', active: false },
  { label: 'Sun', date: '20', active: false },
]

const TIME_ROWS = ['11:30 AM', '12:30 PM', '06:00 PM', '07:00 PM']

const INITIAL_GRID = [
  [null, null, 'lunch', null, null, null, null],
  ['lunch', null, 'lunch', 'lunch', null, null, null],
  [null, 'dinner', null, null, null, null, null],
  [null, null, null, null, 'dinner', null, null],
]

/** 仮データ: 10人以上が登録しているスロット（row, col は TIME_ROWS × DAYS の 0 始まり） */
const HIGH_DEMAND_KEYS = new Set(['0,1', '0,4', '1,5', '2,3', '3,6'])

function isHighDemandSlot(row, col) {
  return HIGH_DEMAND_KEYS.has(`${row},${col}`)
}

function columnHasHighDemand(col) {
  for (let r = 0; r < TIME_ROWS.length; r += 1) {
    if (isHighDemandSlot(r, col)) return true
  }
  return false
}

export default function SetAvailability() {
  const navigate = useNavigate()
  const [grid, setGrid] = useState(() => INITIAL_GRID.map((row) => [...row]))
  const [picker, setPicker] = useState(null)

  const closePicker = () => setPicker(null)

  useEffect(() => {
    if (!picker) return
    const onKey = (e) => {
      if (e.key === 'Escape') setPicker(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [picker])

  const setCellMeal = (row, col, meal) => {
    setGrid((prev) => {
      const next = prev.map((r) => [...r])
      next[row][col] = meal
      return next
    })
    closePicker()
  }

  return (
    <div className="bg-surface font-body text-on-surface antialiased min-h-screen pb-32">
      <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-xl shadow-sm shadow-blue-900/5">
        <div className="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
          <Link to="/discover" className="text-2xl font-black tracking-tight text-blue-700 font-headline">
            Meal Buddy
          </Link>
          <div className="hidden md:flex items-center gap-8">
            <NavLink
              to="/discover"
              className={({ isActive }) =>
                `font-medium px-3 py-1 rounded-lg transition-colors ${
                  isActive ? 'text-blue-800 font-bold border-b-2 border-blue-600' : 'text-slate-500 hover:bg-blue-50'
                }`
              }
            >
              Discover
            </NavLink>
            <NavLink
              to="/availability"
              className={({ isActive }) =>
                `font-medium px-3 py-1 rounded-lg transition-colors ${
                  isActive ? 'text-blue-800 font-bold border-b-2 border-blue-600' : 'text-slate-500 hover:bg-blue-50'
                }`
              }
            >
              Availability
            </NavLink>
            <NavLink
              to="/matches"
              className={({ isActive }) =>
                `font-medium px-3 py-1 rounded-lg transition-colors ${
                  isActive ? 'text-blue-800 font-bold border-b-2 border-blue-600' : 'text-slate-500 hover:bg-blue-50'
                }`
              }
            >
              Matches
            </NavLink>
            <NavLink
              to="/welcome"
              className={({ isActive }) =>
                `font-medium px-3 py-1 rounded-lg transition-colors ${
                  isActive ? 'text-blue-800 font-bold border-b-2 border-blue-600' : 'text-slate-500 hover:bg-blue-50'
                }`
              }
            >
              Profile
            </NavLink>
          </div>
          <div className="flex items-center gap-4">
            <button type="button" className="p-2 rounded-full hover:bg-blue-50 transition-all active:scale-95">
              <MaterialIcon name="notifications" className="text-on-surface-variant" />
            </button>
            <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-primary-container">
              <img alt="" className="w-full h-full object-cover" src={PROFILE} />
            </div>
          </div>
        </div>
      </header>

      <main className="pt-24 pb-32 max-w-7xl mx-auto px-6">
        <div className="mb-12 relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-primary to-primary-dim p-8 md:p-12 text-on-primary">
          <div className="relative z-10 max-w-2xl">
            <h1 className="font-headline font-extrabold text-4xl md:text-5xl tracking-tight mb-4">
              When are we eating?
            </h1>
            <p className="text-lg opacity-90 font-medium mb-6">
              Select your preferred meal times for the upcoming week. We&apos;ll match you with students who share
              your schedule and culinary vibes.
            </p>
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2 bg-white/20 backdrop-blur-md px-4 py-2 rounded-full">
                <MaterialIcon name="restaurant" className="text-[18px]" />
                <span className="text-sm font-semibold">3 Matches Pending</span>
              </div>
              <div className="flex items-center gap-2 bg-white/20 backdrop-blur-md px-4 py-2 rounded-full">
                <MaterialIcon name="schedule" className="text-[18px]" />
                <span className="text-sm font-semibold">Updated 2h ago</span>
              </div>
            </div>
          </div>
          <div className="absolute -right-16 -bottom-16 w-80 h-80 opacity-20 pointer-events-none">
            <MaterialIcon name="calendar_month" className="text-[320px]" />
          </div>
        </div>

        <div className="bg-surface-container-low p-6 md:p-10 lg:p-12 rounded-[2rem] overflow-x-auto no-scrollbar w-full">
          <div className="w-full min-w-[min(100%,42rem)] md:min-w-0 max-w-full mx-auto">
            <div className="grid grid-cols-8 mb-8 md:mb-10 border-b border-outline-variant/10 pb-6 gap-1">
              <div className="col-span-1" />
              {DAYS.map((d, colIndex) => {
                const colHot = columnHasHighDemand(colIndex)
                return (
                  <div key={d.label} className="text-center px-0.5">
                    <span
                      className={`block text-[10px] md:text-xs font-bold uppercase tracking-widest mb-1 md:mb-2 ${
                        d.active ? 'text-primary' : 'text-outline'
                      }`}
                    >
                      {d.label}
                    </span>
                    <span
                      className={`relative inline-flex flex-col items-center gap-1 text-2xl md:text-3xl lg:text-4xl font-bold font-headline ${
                        d.active ? 'text-primary' : 'text-on-surface'
                      }`}
                    >
                      {d.date}
                      {colHot ? (
                        <span
                          className="rounded-full bg-amber-500/90 px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider text-white md:text-[10px]"
                          title="This day has a high-demand time slot"
                        >
                          Hot
                        </span>
                      ) : null}
                    </span>
                  </div>
                )
              })}
            </div>

            <div className="space-y-3 md:space-y-4">
              {TIME_ROWS.map((time, rowIndex) => (
                <div key={time} className="grid grid-cols-8 items-center gap-1 md:gap-2">
                  <div className="col-span-1 text-right pr-2 md:pr-4 text-[10px] md:text-xs font-bold text-outline whitespace-nowrap">
                    {time}
                  </div>
                  {grid[rowIndex].map((cell, colIndex) => {
                    const highDemand = isHighDemandSlot(rowIndex, colIndex) && !cell
                    return (
                      <div key={colIndex} className="p-0.5 md:p-1 min-w-0">
                        <button
                          type="button"
                          onClick={() => setPicker({ row: rowIndex, col: colIndex })}
                          className={`w-full min-h-[3.25rem] h-16 md:h-20 lg:h-[5.5rem] flex flex-col items-center justify-center gap-0.5 rounded-[1.75rem] md:rounded-[2rem] transition-all shadow-sm ${
                            cell === 'lunch'
                              ? 'bg-secondary-container text-secondary ring-0'
                              : cell === 'dinner'
                                ? 'bg-blue-900 text-white shadow-blue-900/25 ring-0'
                                : highDemand
                                  ? 'bg-amber-100 text-amber-950 ring-2 ring-amber-500/90 shadow-md shadow-amber-500/15 hover:bg-amber-200/90'
                                  : 'bg-surface-container-highest hover:bg-primary-container/30 ring-0'
                          }`}
                        >
                          {cell ? (
                            <span className="text-[10px] md:text-xs font-extrabold uppercase tracking-wide">
                              {cell === 'lunch' ? 'Lunch' : 'Dinner'}
                            </span>
                          ) : highDemand ? (
                            <>
                              <MaterialIcon name="groups" className="text-lg text-amber-800 md:text-xl" />
                              <span className="text-[9px] md:text-[10px] font-extrabold uppercase tracking-wide text-amber-950">
                                10+ joined
                              </span>
                            </>
                          ) : null}
                        </button>
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-12 md:mt-14 flex flex-col sm:flex-row justify-between items-center gap-6">
              <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-surface-container-highest rounded-sm" />
                  <span className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">
                    Unavailable
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded-sm bg-amber-100 ring-2 ring-amber-500/90" />
                  <span className="text-xs font-bold text-amber-900 uppercase tracking-wider">10+ joined</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-secondary-container rounded-sm" />
                  <span className="text-xs font-bold text-secondary uppercase tracking-wider">Lunch</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-900 rounded-sm" />
                  <span className="text-xs font-bold text-blue-900 uppercase tracking-wider">Dinner</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate('/matches')}
                className="bg-primary hover:bg-primary-dim text-on-primary font-headline font-bold px-10 py-4 rounded-2xl transition-all shadow-lg shadow-primary/20 flex items-center gap-3 active:scale-95"
              >
                <span>Submit Availability</span>
                <MaterialIcon name="arrow_forward" />
              </button>
          </div>
        </div>

        {picker ? (
          <div
            role="presentation"
            className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center bg-inverse-surface/40 backdrop-blur-sm p-4"
            onClick={closePicker}
          >
            <div
              role="dialog"
              aria-modal="true"
              aria-labelledby="meal-picker-title"
              className="w-full max-w-sm bg-surface-container-lowest rounded-[2rem] p-6 shadow-2xl border border-outline-variant/20"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 id="meal-picker-title" className="font-headline font-bold text-lg text-on-surface mb-1">
                Choose meal type
              </h3>
              <p className="text-sm text-on-surface-variant mb-6">
                {DAYS[picker.col].label} {DAYS[picker.col].date} · {TIME_ROWS[picker.row]}
              </p>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <button
                  type="button"
                  onClick={() => setCellMeal(picker.row, picker.col, 'lunch')}
                  className="py-4 rounded-2xl font-headline font-bold text-sm uppercase bg-secondary-container text-secondary hover:opacity-90 transition-opacity"
                >
                  Lunch
                </button>
                <button
                  type="button"
                  onClick={() => setCellMeal(picker.row, picker.col, 'dinner')}
                  className="py-4 rounded-2xl font-headline font-bold text-sm uppercase bg-blue-900 text-white hover:bg-blue-950 transition-colors"
                >
                  Dinner
                </button>
              </div>
              <button
                type="button"
                onClick={() => setCellMeal(picker.row, picker.col, null)}
                className="w-full py-3 rounded-xl text-sm font-semibold text-on-surface-variant hover:bg-surface-container-high transition-colors"
              >
                Clear slot
              </button>
              <button
                type="button"
                onClick={closePicker}
                className="w-full mt-2 py-2 text-sm font-medium text-outline hover:text-on-surface"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : null}
      </main>

      <nav className="md:hidden fixed bottom-0 left-0 w-full bg-white/90 backdrop-blur-lg shadow-[0_-8px_24px_rgba(31,45,81,0.08)] rounded-t-[2.5rem] z-50 flex justify-around items-center px-4 pb-6 pt-3">
        <Link to="/discover" className="flex flex-col items-center justify-center text-slate-400 px-5 py-2 hover:text-blue-600">
          <MaterialIcon name="explore" />
          <span className="font-body text-[11px] font-semibold">Discover</span>
        </Link>
        <Link
          to="/availability"
          className="flex flex-col items-center justify-center bg-orange-100 text-orange-900 rounded-full px-5 py-2 transition-all active:scale-90 duration-150"
        >
          <MaterialIcon name="calendar_today" filled />
          <span className="font-body text-[11px] font-semibold">Availability</span>
        </Link>
        <Link to="/matches" className="flex flex-col items-center justify-center text-slate-400 px-5 py-2 hover:text-blue-600">
          <MaterialIcon name="group" />
          <span className="font-body text-[11px] font-semibold">Matches</span>
        </Link>
        <Link to="/welcome" className="flex flex-col items-center justify-center text-slate-400 px-5 py-2 hover:text-blue-600">
          <MaterialIcon name="person" />
          <span className="font-body text-[11px] font-semibold">Profile</span>
        </Link>
      </nav>
    </div>
  )
}
