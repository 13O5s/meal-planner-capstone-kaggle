import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  User,
  Package,
  ClipboardList,
  ShoppingCart,
  History,
  Settings,
  ChevronLeft,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/profile', icon: User, label: 'Profile' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/meal-plans', icon: ClipboardList, label: 'Meal Plans' },
  { to: '/shopping-lists', icon: ShoppingCart, label: 'Shopping Lists' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const user = useAuthStore((s) => s.user)
  return (
    <aside
      className={cn(
        'flex flex-col bg-sidebar border-r border-border transition-all duration-300 h-screen shrink-0',
        collapsed ? 'w-[72px]' : 'w-[260px]'
      )}
    >
      <div className={cn(
        'flex items-center h-[72px] border-b border-border shrink-0',
        collapsed ? 'justify-center px-0' : 'px-5'
      )}>
        {!collapsed && (
          <div className="flex items-center gap-2.5 flex-1">
            <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-on-primary" />
            </div>
            <span className="text-base font-bold text-text tracking-tight">MealPlanner</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className={cn(
            'p-2 rounded-xl hover:bg-sidebar-hover transition-colors',
            collapsed && 'mx-auto'
          )}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeft
            className={cn(
              'w-4 h-4 text-text-muted transition-transform',
              collapsed && 'rotate-180'
            )}
          />
        </button>
      </div>

      <nav className="flex-1 py-4 space-y-1 overflow-y-auto px-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-text-muted hover:bg-sidebar-hover hover:text-text',
                collapsed && 'justify-center px-2'
              )
            }
            title={collapsed ? item.label : undefined}
          >
            <item.icon className="w-5 h-5 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 rounded-xl bg-surface-variant p-3">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center shrink-0">
            <User className="w-4 h-4 text-primary" />
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-text truncate">{user?.email?.split('@')[0] || 'User'}</p>
              <p className="text-[11px] text-text-muted">Signed in</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
