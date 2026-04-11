/* eslint-disable react-refresh/only-export-components -- Context と usePreferences はセットで提供 */
import { createContext, useCallback, useContext, useMemo, useReducer } from 'react'

/** Welcome / Dining で共通の料理ラベル（表示順） */
export const WELCOME_CUISINE_LABELS = [
  'Italian',
  'Japanese',
  'Mexican',
  'Indian',
  'Mediterranean',
  'Thai',
  'Korean',
  'Vietnamese',
]

/** Welcome / Dining で共通の食事制限ラベル（表示順）。Low Carb は含めない */
export const WELCOME_DIETARY_LABELS = [
  'Vegetarian',
  'Vegan',
  'Gluten-Free',
  'Nut Allergy',
  'Dairy-Free',
  'Halal',
]

const VALID_WELCOME_LABEL = new Set(WELCOME_CUISINE_LABELS)

/** 表示ラベル → コンテキスト用 cuisine id（小文字） */
export function cuisineLabelToId(label) {
  return label.toLowerCase()
}

/** cuisine id → Welcome 表示ラベル */
export const CUISINE_ID_TO_LABEL = Object.fromEntries(
  WELCOME_CUISINE_LABELS.map((label) => [cuisineLabelToId(label), label]),
)

function diningIdsFromWelcomeLabels(labels) {
  const ids = new Set()
  for (const l of labels) {
    if (VALID_WELCOME_LABEL.has(l)) ids.add(cuisineLabelToId(l))
  }
  return ids
}

function tierFromAmount(n) {
  if (n <= 33) return 'budget'
  if (n <= 66) return 'value'
  return 'premium'
}

const TIER_DEFAULT_AMOUNT = { budget: 20, value: 50, premium: 85 }

const initialWelcome = ['Italian', 'Mediterranean']

const initialState = {
  welcomeCuisineLabels: initialWelcome,
  diningCuisineIds: [...diningIdsFromWelcomeLabels(initialWelcome)],
  budgetAmount: 45,
  budgetTier: tierFromAmount(45),
  dietaryKeys: ['gluten-free'],
}

function reducer(state, action) {
  switch (action.type) {
    case 'toggleWelcomeCuisine': {
      const s = new Set(state.welcomeCuisineLabels)
      if (s.has(action.label)) s.delete(action.label)
      else s.add(action.label)
      const labels = [...s]
      return {
        ...state,
        welcomeCuisineLabels: labels,
        diningCuisineIds: [...diningIdsFromWelcomeLabels(labels)],
      }
    }
    case 'toggleDiningCuisine': {
      const s = new Set(state.diningCuisineIds)
      const id = action.id
      const label = CUISINE_ID_TO_LABEL[id]
      if (!label) return state

      const labels = new Set(state.welcomeCuisineLabels)
      if (s.has(id)) {
        s.delete(id)
        labels.delete(label)
      } else {
        s.add(id)
        labels.add(label)
      }

      return {
        ...state,
        diningCuisineIds: [...s],
        welcomeCuisineLabels: [...labels],
      }
    }
    case 'setBudgetAmount': {
      const n = action.value
      return {
        ...state,
        budgetAmount: n,
        budgetTier: tierFromAmount(n),
      }
    }
    case 'setBudgetTier': {
      const tier = action.tier
      return {
        ...state,
        budgetTier: tier,
        budgetAmount: TIER_DEFAULT_AMOUNT[tier] ?? state.budgetAmount,
      }
    }
    case 'toggleDietary': {
      const next = new Set(state.dietaryKeys)
      if (next.has(action.key)) next.delete(action.key)
      else next.add(action.key)
      return { ...state, dietaryKeys: [...next] }
    }
    default:
      return state
  }
}

const PreferencesContext = createContext(null)

export function PreferencesProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const toggleWelcomeCuisine = useCallback((label) => {
    dispatch({ type: 'toggleWelcomeCuisine', label })
  }, [])

  const toggleDiningCuisine = useCallback((id) => {
    dispatch({ type: 'toggleDiningCuisine', id })
  }, [])

  const setBudgetAmount = useCallback((value) => {
    dispatch({ type: 'setBudgetAmount', value })
  }, [])

  const setBudgetTier = useCallback((tier) => {
    dispatch({ type: 'setBudgetTier', tier })
  }, [])

  const toggleDietary = useCallback((key) => {
    dispatch({ type: 'toggleDietary', key })
  }, [])

  const value = useMemo(
    () => ({
      welcomeCuisineLabels: state.welcomeCuisineLabels,
      diningCuisineIds: state.diningCuisineIds,
      budgetAmount: state.budgetAmount,
      budgetTier: state.budgetTier,
      dietaryKeys: state.dietaryKeys,
      toggleWelcomeCuisine,
      toggleDiningCuisine,
      setBudgetAmount,
      setBudgetTier,
      toggleDietary,
    }),
    [
      state.welcomeCuisineLabels,
      state.diningCuisineIds,
      state.budgetAmount,
      state.budgetTier,
      state.dietaryKeys,
      toggleWelcomeCuisine,
      toggleDiningCuisine,
      setBudgetAmount,
      setBudgetTier,
      toggleDietary,
    ],
  )

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>
}

export function usePreferences() {
  const ctx = useContext(PreferencesContext)
  if (!ctx) throw new Error('usePreferences must be used within PreferencesProvider')
  return ctx
}
