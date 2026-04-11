import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  // eslint-disable-next-line no-console
  console.error(
    '[supabase] Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. ' +
      'Check frontend/.env.local and restart the dev server.'
  )
}

/**
 * Defensive storage adapter for Supabase Auth.
 *
 * Claude Preview / some iframe sandboxes have tiny localStorage quotas and
 * will throw QuotaExceededError when the Supabase SDK tries to persist the
 * session. When that happens we fall back to an in-memory Map — the user
 * stays signed in for the current tab, they just have to re-login on reload.
 *
 * Normal browsers use localStorage as usual.
 */
function createResilientStorage() {
  const memory = new Map()

  const readLS = (key) => {
    try {
      return globalThis.localStorage?.getItem(key) ?? null
    } catch {
      return null
    }
  }

  const writeLS = (key, value) => {
    try {
      globalThis.localStorage?.setItem(key, value)
      return true
    } catch (err) {
      // QuotaExceededError or SecurityError — fall back to memory.
      // eslint-disable-next-line no-console
      console.warn(
        '[supabase storage] localStorage.setItem failed, using memory:',
        err?.name || err
      )
      return false
    }
  }

  const removeLS = (key) => {
    try {
      globalThis.localStorage?.removeItem(key)
    } catch {
      // ignore
    }
  }

  return {
    getItem: (key) => {
      if (memory.has(key)) return memory.get(key)
      return readLS(key)
    },
    setItem: (key, value) => {
      memory.set(key, value)
      writeLS(key, value)
    },
    removeItem: (key) => {
      memory.delete(key)
      removeLS(key)
    },
  }
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: createResilientStorage(),
    storageKey: 'jarvis-admin-auth',
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})
