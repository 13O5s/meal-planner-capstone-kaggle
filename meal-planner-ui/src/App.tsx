import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopBar } from '@/components/layout/TopBar'
import { DashboardPage } from '@/pages/DashboardPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { InventoryPage } from '@/pages/InventoryPage'
import { MealPlansPage } from '@/pages/MealPlansPage'
import { ShoppingListsPage } from '@/pages/ShoppingListsPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { SetupProfilePage } from '@/pages/SetupProfilePage'
import { useAuthStore } from '@/stores/auth-store'
import { getUserProfile } from '@/lib/api'

function ProtectedLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-background dark:bg-background-dark">
      <div className="hidden lg:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        >
          <div className="absolute left-0 top-0 h-full" onClick={(e) => e.stopPropagation()}>
            <Sidebar
              collapsed={false}
              onToggle={() => setMobileSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <TopBar onMenuClick={() => setMobileSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/meal-plans" element={<MealPlansPage />} />
            <Route path="/shopping-lists" element={<ShoppingListsPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    if (!user || user.profile_complete) return
    let cancelled = false
    setChecking(true)
    getUserProfile(user.user_id).then((profile) => {
      if (cancelled) return
      if (profile) {
        setUser({ ...user, profile_complete: true })
      }
    }).catch(() => {
      // ignore
    }).finally(() => {
      if (!cancelled) setChecking(false)
    })
    return () => { cancelled = true }
  }, [])

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background dark:bg-background-dark">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-body text-outline dark:text-outline-dark">Checking profile...</p>
        </div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      {!user ? (
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      ) : !user.profile_complete ? (
        <Routes>
          <Route path="/setup-profile" element={<SetupProfilePage />} />
          <Route path="*" element={<Navigate to="/setup-profile" replace />} />
        </Routes>
      ) : (
        <ProtectedLayout />
      )}
    </BrowserRouter>
  )
}
