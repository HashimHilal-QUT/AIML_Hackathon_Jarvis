import { Link } from 'react-router-dom'
import { MaterialIcon } from '../components/MaterialIcon'

const FOOD_IMG =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuCgDZXFJZMNw0KFI01eLkTX5-Kwp4RHrHfgOBIlLrpolUlCadkigFgA_y1fMa_lkOkMSkxTCGY9gWvJ8ExR0cvpJeIMM4zpoqTlTwYvK14IGXju7QQPpwhbCyHjkwqNc32Ei-7p115YwavN1xz4nkqmYiVZdpvEtLSO_kDhl3XSSHnm90rAdPRC9UjroYXRnxyDnwfXpRtSvfNthbMXVYAJVS5XhUYGOIDI64NwjMXi9bXuOHX_mJqRjZcuPE-LzlIxzK1q_Rmqt0MU'
const SALAD_IMG =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuCkpjxXYbzRHIfmTXAAWgUrSsmNcu24q9y4Ibn3WYZPFX_SJxKjEKFkPmB2TCJlMWXnSbSyr_73f868VBZh41boSWaznwuZ8sgEpdvKzDjpUPb2EE2fsupSthvP7P1QqVdAtGKyWHvSq_C70q9_78MWejDYhYFqSoA3NVpfhtyZM8l1fXu334hH4FBe7K2ZQxKT31P4-uxvElq_ouA6WnwdMVZTjoQqMxredSUWMWbw1R_Dcqc7LbIMO5HfVfZzQA-LFas3fNv5dfBr'
const AVATARS = [
  'https://lh3.googleusercontent.com/aida-public/AB6AXuAdqj9aNuSMgaBOlKQtx1cjUKQDfBfAuK6TAJRK7SJtZPvTRX2qRIqpVL-zTypPfGwg28wFfu8--fIy68MGMF7G7Qs9oNNSCPhZE3-0ru_HgBx0oNzLAhwM2VI3bqKh7tADjOigiNKeu2_tpmsR6pXjsX_9rZdFrop4nSlT1T6vLCA2cnYGmgmUtjqr1W1Hxgvx9RyplfvnfMeMnOe4PTunldXBF3xhFBMhP_9xIFECdMpLCcz1k0qxwpnE6_tT_9T9NaWMc8duQ9z8',
  'https://lh3.googleusercontent.com/aida-public/AB6AXuAiMILzMvrYH-dsUyj5rpThh27Gk7p57pjF7MDiXodcC6xx8hZweMI6xRWiAqk69p2V9N8OBlN9t20V7rqOfdNwwWL28QC5mSeMRo6rVkUhqV3ZOmpEhTZgyo3fhNUgoVOkygDdeff2WVY2OULEhsMDmM9OtZiSYC-ifymfg6NP5Oesk8BDHZd0Alv4JIgQSBKixMKAM-UgxxDv0uJMnuD9YyPwYYlaS_sxqS2ctkEjAPALFHo4WHDp6c8N6dTIN1zCx9lT39BjCrwU',
  'https://lh3.googleusercontent.com/aida-public/AB6AXuDBFMPZWjDya7u9wyo9UmK1H5Q7KYFPZmNZsmc_4Q6_k2ViaEvrVi--qHG9pP_NUmBwErrVS8-HzB0aPqP_qnvlujN40VxSpLX7qEnRptbxmp-_iNPZ_7m8je3XwR0Lgc9h718_cKs20hFD02ldoIWqNA6MxjVU_CoAQBKJEBNaQ1n3IBj0oYf1NGtZYkgbqwCPtftRWBYRwtnxqzA1rb-Iacr9KnLVNilJapvS0GJoxAto9uthvdHuA0vBgDe0kNyJPsqrlffe8vtR',
]

export default function WelcomeOnboarding() {
  return (
    <main className="min-h-screen max-w-7xl mx-auto px-6 pt-12 pb-24 lg:pt-20 bg-surface text-on-surface selection:bg-primary-container">
      <header className="mb-16 max-w-3xl">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-primary leading-tight mb-6 font-headline">
          Welcome to Meal Buddy!{' '}
          <span className="text-secondary">Tell us what you crave.</span>
        </h1>
        <p className="text-lg md:text-xl text-on-surface-variant font-medium leading-relaxed">
          Let&apos;s personalize your experience to find your perfect culinary matches. Your journey
          to better dining starts with just a few details.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        <section className="md:col-span-8 bg-surface-container-low rounded-[2rem] p-8 relative overflow-hidden group">
          <div className="absolute -top-12 -right-12 w-48 h-48 bg-secondary-container/20 rounded-full blur-3xl group-hover:bg-secondary-container/40 transition-colors" />
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-8">
              <MaterialIcon name="restaurant" className="text-secondary text-3xl" />
              <h2 className="text-2xl font-bold tracking-tight font-headline">Cuisine Preferences</h2>
            </div>
            <div className="flex flex-wrap gap-3">
              {['Italian', 'Japanese', 'Mexican', 'Indian', 'Mediterranean', 'Thai', 'Korean', 'Vietnamese'].map(
                (label) => {
                  const selected = label === 'Italian' || label === 'Mediterranean'
                  return (
                    <button
                      key={label}
                      type="button"
                      className={
                        selected
                          ? 'px-6 py-3 bg-tertiary-container text-on-tertiary-container font-bold rounded-full transition-transform active:scale-95'
                          : 'px-6 py-3 bg-surface-container-highest text-on-surface-variant font-medium rounded-full hover:bg-surface-container-high transition-colors'
                      }
                    >
                      {label}
                    </button>
                  )
                },
              )}
            </div>
          </div>
          <div className="mt-12 -mb-8 -mr-8 flex justify-end">
            <img
              alt=""
              className="w-64 h-40 object-cover rounded-tl-[2rem] shadow-xl rotate-3 hover:rotate-0 transition-transform duration-500"
              src={FOOD_IMG}
            />
          </div>
        </section>

        <section className="md:col-span-4 bg-primary text-on-primary rounded-[2rem] p-8 flex flex-col justify-between shadow-2xl">
          <div>
            <div className="flex items-center gap-3 mb-8">
              <MaterialIcon name="payments" className="text-primary-container text-3xl" />
              <h2 className="text-2xl font-bold tracking-tight font-headline">Per Meal</h2>
            </div>
            <p className="text-primary-container font-medium mb-12">
              Set your daily spending limit for the best recommendations.
            </p>
          </div>
          <div className="space-y-6">
            <div className="relative pt-1">
              <input
                className="w-full h-2 bg-primary-dim rounded-lg appearance-none cursor-pointer accent-secondary"
                max={100}
                min={10}
                type="range"
                defaultValue={45}
              />
              <div className="flex justify-between mt-4 font-bold font-headline">
                <span>$10</span>
                <span className="text-2xl text-secondary">$45</span>
                <span>$100</span>
              </div>
            </div>
          </div>
        </section>

        <section className="md:col-span-12 bg-surface-container-low rounded-[2rem] p-8 relative overflow-hidden">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <MaterialIcon name="clinical_notes" className="text-tertiary text-3xl" />
                <h2 className="text-2xl font-bold tracking-tight font-headline">Requirements &amp; Allergies</h2>
              </div>
              <p className="text-on-surface-variant mb-8 font-medium">
                We take safety seriously. Select any dietary needs or allergies so we can filter your
                menu safely.
              </p>
              <div className="grid grid-cols-2 gap-4">
                {['Vegetarian', 'Vegan', 'Gluten-Free', 'Nut Allergy', 'Dairy-Free', 'Halal'].map((label) => (
                  <label
                    key={label}
                    className="flex items-center gap-3 p-4 bg-surface-container-highest rounded-2xl cursor-pointer hover:bg-surface-container-high transition-colors group"
                  >
                    <input
                      className="w-5 h-5 rounded border-outline text-tertiary focus:ring-tertiary"
                      type="checkbox"
                      defaultChecked={label === 'Gluten-Free'}
                    />
                    <span className="font-semibold text-on-surface group-hover:text-primary transition-colors">
                      {label}
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="hidden md:block relative h-full min-h-[300px]">
              <div className="absolute inset-0 bg-tertiary-container rounded-[2rem] overflow-hidden">
                <img alt="" className="w-full h-full object-cover mix-blend-overlay opacity-60" src={SALAD_IMG} />
                <div className="absolute inset-0 flex items-center justify-center p-8 text-center">
                  <div className="bg-white/80 backdrop-blur-md p-6 rounded-[2rem]">
                    <p className="text-tertiary-dim font-bold text-lg leading-tight">
                      &quot;Health is not just what you eat, but how you feel.&quot;
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <footer className="mt-20 flex flex-col md:flex-row items-center justify-between gap-8 border-t border-transparent pt-12">
        <div className="flex items-center gap-6">
          <div className="flex -space-x-3">
            {AVATARS.map((src, i) => (
              <img
                key={i}
                alt=""
                className="w-12 h-12 rounded-full border-4 border-surface object-cover"
                src={src}
              />
            ))}
          </div>
          <p className="text-on-surface-variant font-medium">Join 2,000+ students already dining better.</p>
        </div>
        <Link
          to="/dining-preferences"
          className="w-full md:w-auto px-12 py-5 bg-primary text-on-primary text-xl font-extrabold rounded-2xl shadow-lg hover:bg-primary-dim transition-all active:scale-95 flex items-center justify-center gap-3 group font-headline"
        >
          Get Started
          <MaterialIcon name="arrow_forward" className="transition-transform group-hover:translate-x-2" />
        </Link>
      </footer>

      <div className="fixed top-0 right-0 -z-10 w-1/3 h-screen bg-gradient-to-l from-surface-container-high/30 to-transparent pointer-events-none" />
      <div className="fixed bottom-0 left-0 -z-10 w-64 h-64 bg-secondary-container/10 rounded-full blur-[100px] pointer-events-none" />
    </main>
  )
}
