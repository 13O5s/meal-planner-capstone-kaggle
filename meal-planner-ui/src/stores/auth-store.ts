import { create } from 'zustand'

export interface AuthUser {
  user_id: string
  email: string
  profile_complete: boolean
}

interface AuthState {
  user: AuthUser | null
  loading: boolean
  setUser: (user: AuthUser | null) => void
  setLoading: (loading: boolean) => void
  logout: () => void
}

function loadUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem('meal_planner_user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveUser(user: AuthUser | null) {
  if (user) {
    localStorage.setItem('meal_planner_user', JSON.stringify(user))
  } else {
    localStorage.removeItem('meal_planner_user')
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: loadUser(),
  loading: false,
  setUser: (user) => {
    saveUser(user)
    set({ user })
  },
  setLoading: (loading) => set({ loading }),
  logout: () => {
    localStorage.removeItem('meal_planner_user')
    localStorage.removeItem('meal_planner_last_session')
    set({ user: null })
  },
}))
