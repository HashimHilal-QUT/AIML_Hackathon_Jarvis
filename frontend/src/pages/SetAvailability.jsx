import { Link, NavLink } from 'react-router-dom'
import { MaterialIcon } from '../components/MaterialIcon'

const PROFILE =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuCHfIX5N9uZQ4CL661nKVqWJpPhoZW1V_7uPvvQGmx2QyZmzjbuisR4Vri_QK0x-Ji9qGsLPnpiSuB02-89f-5TL2SzO7lM2ElSJUgRiMiNm74aUYWPUqXJNWQwbvu543_9vLvGyIgQzHykgS6TzzmQKlKNpFIiYYfH8h18nAXInpp_snPO-e16Zz9RylBs2cKRMh2nTB0lt7JndCjnXK_QAuN34rAyJ4wd4h8cDKmZSmDSXF4CEZyS-HXjF4B9vPQXtAo616r7ZRU'

const BUDDIES = [
  {
    name: 'Sarah Jenkins',
    major: 'Philosophy Major',
    when: 'Available Wednesday, 12:30 PM',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDQlvtA_DUuNi0rsZWJPFCPRucSg9ks5QySIP0eRU-dsfBgnnNcVRwkZ12zOe5vMm6ej2pPYddvQhqV9cbFW8F81KyXYe85BXDvj8C9alCnrn7n8oYxBUZzO6z-JlYGEZ7aU8Tt9lgk23y26za1q35yfEeSAYzkP_xdQNReUauBxXHhdx3QE1JDl5qF2JnDD0MTeoyRpI_aM-7finnTQZBOjWopr8luCbqOdjiZmCLOiodl6HAeEz_X1ZJhsNzkNb-o_KnP1tqmFC8',
  },
  {
    name: 'Marcus Thorne',
    major: 'Computer Science',
    when: 'Available Tuesday, 06:00 PM',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBNhq7JhPFK4NkL3WHn-zeOsMnsZ4XYsiCiVOZmFtmqjiNGPHYDsyEkDAQntwS6g2NEk2sw-4TTNEQAxCbz9O38MdLV8jIIbgnxygm-it2e7bT48aCcCv-dYceMI9AnOE6zqBAryDyuG9sryY75qXDGuNtyMIKchk7bM356zkiYOoWim6do_WjoEIRXd1N9ZQddYgkoZmfG9A3XDJkp3r7hPC-7YVWJoIfq9szxewllM6F_482jvDUIbYsIIJYp6iExVRdloIyLVYE',
  },
  {
    name: 'Lila Kim',
    major: 'Fine Arts',
    when: 'Available Wednesday, 12:30 PM',
    img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDe02hOi3pEHTTOUNOPiunwtvDc8CVlpJ1XCGUKtJloZF-mFJqgOYDl1Zij6aLFVwsuLTtlI09KRPR13K6qB8hxBOtqizcQOfSaTqEMYPWmnSmwHCUyhOLRGAVGu559MBKHaF_ToMRm1T1dYf0H-d8KekdmryR8PTnOTYc_f6cEZZiJJE5WQ32WIxrKzQOIPXoycK6OQdmPzzZSEI8PI5mIFAHUpatItwXUsO5rn88sugi5SWtZ7YGG1UKnvpfqDnhTadhWN3T_S_c',
  },
]

const DAYS = [
  { label: 'Mon', date: '14', active: false },
  { label: 'Tue', date: '15', active: false },
  { label: 'Wed', date: '16', active: true },
  { label: 'Thu', date: '17', active: false },
  { label: 'Fri', date: '18', active: false },
  { label: 'Sat', date: '19', active: false },
  { label: 'Sun', date: '20', active: false },
]

const GRID = [
  {
    time: '11:30 AM',
    cells: [null, null, 'lunch', null, null, null, null],
  },
  {
    time: '12:30 PM',
    cells: ['lunch', null, 'lunch', 'lunch', null, null, null],
  },
  {
    time: '06:00 PM',
    cells: [null, 'dinner', null, null, null, null, null],
  },
  {
    time: '07:00 PM',
    cells: [null, null, null, null, 'dinner', null, null],
  },
]

export default function SetAvailability() {
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

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-surface-container-low p-6 rounded-[2rem]">
              <h3 className="font-headline font-bold text-lg mb-4 text-primary">Preferences</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-outline mb-2">
                    Campus Location
                  </label>
                  <select className="w-full bg-surface-container-highest border-none rounded-xl px-3 py-2 text-on-surface focus:ring-2 focus:ring-primary/20">
                    <option>Main Quad Cafeteria</option>
                    <option>Library Lounge</option>
                    <option>Science Park Hub</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-outline mb-2">
                    Match Style
                  </label>
                  <div className="grid grid-cols-1 gap-2">
                    <label className="flex items-center gap-3 p-3 bg-surface-container-lowest rounded-[2rem] cursor-pointer hover:bg-white transition-colors">
                      <input className="text-secondary focus:ring-secondary" defaultChecked name="style" type="radio" />
                      <span className="text-sm font-medium">Quick Bite (30m)</span>
                    </label>
                    <label className="flex items-center gap-3 p-3 bg-surface-container-lowest rounded-[2rem] cursor-pointer hover:bg-white transition-colors">
                      <input className="text-secondary focus:ring-secondary" name="style" type="radio" />
                      <span className="text-sm font-medium">Long Lunch (1h+)</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-tertiary-container/30 p-6 rounded-[2rem]">
              <div className="flex items-start gap-3">
                <MaterialIcon name="tips_and_updates" className="text-tertiary" />
                <div>
                  <h4 className="font-bold text-tertiary text-sm">Pro Tip</h4>
                  <p className="text-xs text-on-tertiary-container mt-1 leading-relaxed">
                    Selecting lunch slots increases match probability by 45%!
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-9 bg-surface-container-low p-6 md:p-8 rounded-[2rem] overflow-x-auto no-scrollbar">
            <div className="min-w-[700px]">
              <div className="grid grid-cols-8 mb-6 border-b border-outline-variant/10 pb-4">
                <div className="col-span-1" />
                {DAYS.map((d) => (
                  <div key={d.label} className="text-center">
                    <span
                      className={`block text-xs font-bold uppercase tracking-widest mb-1 ${
                        d.active ? 'text-primary' : 'text-outline'
                      }`}
                    >
                      {d.label}
                    </span>
                    <span className={`text-xl font-bold ${d.active ? 'text-primary' : 'text-on-surface'}`}>
                      {d.date}
                    </span>
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                {GRID.map((row) => (
                  <div key={row.time} className="grid grid-cols-8 items-center group">
                    <div className="col-span-1 text-right pr-4 text-[10px] font-bold text-outline">{row.time}</div>
                    {row.cells.map((cell, i) => (
                      <div key={i} className="p-1">
                        {cell ? (
                          <button
                            type="button"
                            className="w-full h-14 bg-secondary-container text-secondary flex flex-col items-center justify-center rounded-[2rem] shadow-sm"
                          >
                            <MaterialIcon name="check_circle" className="text-[16px]" filled />
                            <span className="text-[10px] font-bold uppercase">
                              {cell === 'lunch' ? 'Lunch' : 'Dinner'}
                            </span>
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="w-full h-14 bg-surface-container-highest rounded-xl hover:bg-primary-container/30 transition-all"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-12 flex flex-col sm:flex-row justify-between items-center gap-6">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-surface-container-highest rounded-sm" />
                  <span className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">
                    Unavailable
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-secondary-container rounded-sm" />
                  <span className="text-xs font-bold text-secondary uppercase tracking-wider">Your Selection</span>
                </div>
              </div>
              <button
                type="button"
                className="bg-primary hover:bg-primary-dim text-on-primary font-headline font-bold px-10 py-4 rounded-2xl transition-all shadow-lg shadow-primary/20 flex items-center gap-3 active:scale-95"
              >
                <span>Submit Availability</span>
                <MaterialIcon name="arrow_forward" />
              </button>
            </div>
          </div>
        </div>

        <div className="mt-20">
          <h2 className="font-headline font-extrabold text-2xl mb-8 flex items-center gap-3">
            <MaterialIcon name="volunteer_activism" className="text-tertiary" />
            Popular times with your buddies
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {BUDDIES.map((b) => (
              <div
                key={b.name}
                className="bg-surface-container-low p-6 rounded-[2rem] group hover:bg-white transition-all"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-full overflow-hidden">
                    <img alt="" className="w-full h-full object-cover" src={b.img} />
                  </div>
                  <div>
                    <h4 className="font-bold text-on-surface">{b.name}</h4>
                    <p className="text-xs text-outline font-medium">{b.major}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <MaterialIcon name="event_available" className="text-[16px] text-tertiary" />
                  <span className="text-xs font-semibold">{b.when}</span>
                </div>
                <button
                  type="button"
                  className="mt-4 w-full py-2 bg-tertiary-container text-on-tertiary-container rounded-full text-xs font-bold opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  Match Now
                </button>
              </div>
            ))}
          </div>
        </div>
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
