import { Link, NavLink } from 'react-router-dom'
import { MaterialIcon } from '../components/MaterialIcon'

const AVATAR =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuBe3qdZd51UMysEbcnt9tM9vkNvB-YuHftYOozo-0PXUcPaz67CGOE84uimawwd7g_1OIpy32hRBpU-LwMAzCJbJ4Q-AG3bkIZsr2kS5ocXUDslHmvGIO93dkGkdDSN3VSLopFBT00Mu50Td15pH_8tNARc0Or-Vvdn9hltSWP1CvfIyOw4OWB4RjAqteODoKFwWTOS_RIYOThEmS6UZHQhpE0Yq8Y_u2cWm0pNUkl95wr2PAKAK9uILg63lw0o8ecSrsebxNLvzXA'
const COMPANION =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuAgTQlx44zEAdiYO9BkgNs-r9YPkESyiWiwFaGLiTxq5Y-KMb6lMulOwOTbM7Ri453sAI-ePMiU9jTyADXg2K6Aud_5SwIcHwZnSJ_mwMK_z78JW3169j1kqpOG6jV1ys3bC3Cd8097AZUaxSNGz3tnQxAVwJdYY2eWe6i63jtdl1Q1ibsYpUQR8yWkxCGzYkzWQoyk3-VMYPbStv-_261hXr9B-Z0OCuvLMtumkm8BMIbzzC87xkaovrTWKBeatDpb14Sp2XznyVw'
const REST_IMG =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuASvAHABzC2ho9oRy1hlBuyt0Qq-4eqhKddhiFkMfUHfGxzLPJVN7xcS4yTJ1YJxTOeCd7Gm2FUzljHn9g3SFAXSjJ4d-dueJ-GpCL7I_A4OqRqJbPUAqpCkQqhwJNkbl9najj0kzc2SG94xJ0wBeLvkK3Ki6T5l_3qFDXOGRiYosxryv6bHCe1p8Z8z-oNhIHsIKNFdKr5ipON-lVROV-ycUoPJmnVI4jKNm0qieIBKaNA2-i79-K7ciWekNKLCp4fyEx0_cZKiK8'

function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 w-full flex justify-around items-center px-4 pb-6 pt-3 bg-white/90 backdrop-blur-lg shadow-[0_-8px_24px_rgba(31,45,81,0.08)] z-50 rounded-t-[2.5rem]">
      <NavLink
        to="/discover"
        className={({ isActive }) =>
          `flex flex-col items-center justify-center px-5 py-2 ${isActive ? 'text-blue-800' : 'text-slate-400'}`
        }
      >
        <MaterialIcon name="explore" className="mb-1" />
        <span className="font-body text-[11px] font-semibold">Discover</span>
      </NavLink>
      <NavLink
        to="/availability"
        className={({ isActive }) =>
          `flex flex-col items-center justify-center px-5 py-2 ${isActive ? 'text-blue-800' : 'text-slate-400'}`
        }
      >
        <MaterialIcon name="calendar_today" className="mb-1" />
        <span className="font-body text-[11px] font-semibold">Availability</span>
      </NavLink>
      <NavLink
        to="/matches"
        className={({ isActive }) =>
          `flex flex-col items-center justify-center rounded-full px-5 py-2 ${
            isActive ? 'bg-orange-100 text-orange-900' : 'text-slate-400'
          }`
        }
      >
        {({ isActive }) => (
          <>
            <MaterialIcon name="group" className="mb-1" filled={isActive} />
            <span className="font-body text-[11px] font-semibold">Matches</span>
          </>
        )}
      </NavLink>
      <NavLink
        to="/dining-preferences"
        className={({ isActive }) =>
          `flex flex-col items-center justify-center px-5 py-2 ${isActive ? 'text-blue-800' : 'text-slate-400'}`
        }
      >
        <MaterialIcon name="person" className="mb-1" />
        <span className="font-body text-[11px] font-semibold">Profile</span>
      </NavLink>
    </nav>
  )
}

export default function MatchDetails() {
  return (
    <div className="bg-surface text-on-surface font-body min-h-screen pb-24">
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-xl shadow-sm shadow-blue-900/5">
        <div className="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
          <Link to="/discover" className="text-2xl font-black tracking-tight text-blue-700 font-headline">
            Meal Buddy
          </Link>
          <div className="flex items-center gap-4">
            <button type="button" className="p-2 text-slate-500 hover:bg-blue-50 transition-colors rounded-full">
              <MaterialIcon name="notifications" />
            </button>
            <div className="w-10 h-10 rounded-full bg-surface-container-highest overflow-hidden">
              <img alt="" className="w-full h-full object-cover" src={AVATAR} />
            </div>
          </div>
        </div>
      </nav>

      <main className="pt-24 px-6 max-w-2xl mx-auto">
        <section className="mb-10 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-tertiary-container text-on-tertiary-container rounded-full mb-6 font-label font-semibold text-sm">
            <MaterialIcon name="celebration" className="text-lg" />
            Match Found!
          </div>
          <h1 className="font-headline font-extrabold text-4xl text-on-surface leading-tight tracking-tight mb-4">
            You&apos;ve been matched for a meal at <span className="text-secondary">The Terrace Bistro</span> at{' '}
            <span className="text-secondary">12:30 PM</span>!
          </h1>
          <p className="text-on-surface-variant text-lg">
            Your perfect dining companion is waiting. Review the details below to confirm your seat.
          </p>
        </section>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-12">
          <div className="md:col-span-12 bg-surface-container-low rounded-[2rem] p-8 relative overflow-hidden flex flex-col items-center text-center">
            <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-primary/5 rounded-full blur-3xl" />
            <div className="relative z-10">
              <div className="w-32 h-32 rounded-full border-4 border-surface-container-lowest shadow-xl mx-auto mb-6 overflow-hidden">
                <img alt="" className="w-full h-full object-cover" src={COMPANION} />
              </div>
              <h2 className="font-headline font-bold text-2xl mb-1">Sarah Jenkins</h2>
              <p className="text-primary font-semibold mb-4">Senior Architecture Student</p>
              <div className="flex flex-wrap justify-center gap-2 mb-6">
                {['Design', 'Sustainable Tech', 'Coffee Lover'].map((t) => (
                  <span
                    key={t}
                    className="px-4 py-1.5 bg-surface-container-highest rounded-full text-xs font-bold text-on-surface-variant"
                  >
                    {t}
                  </span>
                ))}
              </div>
              <div className="bg-surface-container-lowest/50 p-6 rounded-[2rem] text-left border border-white/20">
                <p className="italic text-on-surface-variant leading-relaxed">
                  &quot;Looking for a quick chat about urban planning or just enjoying some great pasta! I&apos;ve been
                  wanting to try the new menu at The Terrace.&quot;
                </p>
              </div>
            </div>
          </div>

          <div className="md:col-span-7 bg-surface-container-low rounded-[2rem] p-6 flex flex-col justify-between">
            <div>
              <h3 className="font-headline font-bold text-xl mb-4 flex items-center gap-2">
                <MaterialIcon name="restaurant" className="text-secondary" />
                The Terrace Bistro
              </h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-on-surface-variant">
                  <MaterialIcon name="location_on" className="text-lg" />
                  <span className="text-sm">Central Plaza, Level 3</span>
                </div>
                <div className="flex items-center gap-3 text-on-surface-variant">
                  <MaterialIcon name="schedule" className="text-lg" />
                  <span className="text-sm font-semibold">Today, 12:30 PM — 1:30 PM</span>
                </div>
              </div>
            </div>
            <div className="mt-6 rounded-[2rem] overflow-hidden h-32 relative">
              <img alt="" className="w-full h-full object-cover" src={REST_IMG} />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
            </div>
          </div>

          <div className="md:col-span-5 bg-surface-container-low rounded-[2rem] p-6">
            <h3 className="font-headline font-bold text-lg mb-4 flex items-center gap-2">
              <MaterialIcon name="bolt" className="text-tertiary" />
              Why you matched
            </h3>
            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-tertiary/10 flex items-center justify-center shrink-0">
                  <MaterialIcon name="group" className="text-tertiary text-sm" />
                </div>
                <div>
                  <p className="text-sm font-bold">Mutual Network</p>
                  <p className="text-xs text-on-surface-variant">You both know 3 people in the Design faculty.</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center shrink-0">
                  <MaterialIcon name="restaurant_menu" className="text-secondary text-sm" />
                </div>
                <div>
                  <p className="text-sm font-bold">Dietary Harmony</p>
                  <p className="text-xs text-on-surface-variant">Both preferred Vegetarian-friendly options.</p>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mb-20">
          <button
            type="button"
            className="flex-1 bg-primary text-on-primary py-4 px-8 rounded-2xl font-headline font-bold text-lg hover:bg-primary-dim transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
          >
            <MaterialIcon name="check_circle" />
            Accept
          </button>
          <button
            type="button"
            className="flex-1 bg-surface-container-highest text-on-surface-variant py-4 px-8 rounded-2xl font-headline font-bold text-lg hover:bg-surface-container-high transition-all flex items-center justify-center gap-2"
          >
            <MaterialIcon name="cancel" />
            Decline
          </button>
        </div>
      </main>

      <BottomNav />
    </div>
  )
}
