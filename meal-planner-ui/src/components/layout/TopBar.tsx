import { useState, useRef, useEffect, useCallback } from 'react'
import { Bell, User as UserIcon, LogOut, Sparkles, CheckCheck, Clock } from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { useNotificationStore } from '@/stores/notification-store'
import { getNotifications } from '@/lib/api'
import { cn } from '@/lib/utils'

interface TopBarProps {
  onMenuClick: () => void
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const notifications = useNotificationStore((s) => s.notifications)
  const unreadCount = useNotificationStore((s) => s.unreadCount)
  const markAllRead = useNotificationStore((s) => s.markAllRead)
  const setNotifications = useNotificationStore((s) => s.setNotifications)
  const setUnreadCount = useNotificationStore((s) => s.setUnreadCount)
  const connectWs = useNotificationStore((s) => s.connect)
  const disconnectWs = useNotificationStore((s) => s.disconnect)

  const [menuOpen, setMenuOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const notifRef = useRef<HTMLDivElement>(null)

  const fetchNotifications = useCallback(async () => {
    if (!user?.user_id) return
    try {
      const data = await getNotifications(user.user_id)
      if (data.success) {
        setNotifications(data.notifications)
        setUnreadCount(data.unread_count)
      }
    } catch {
      // offline — skip
    }
  }, [user?.user_id, setNotifications, setUnreadCount])

  useEffect(() => {
    if (user?.user_id) {
      fetchNotifications()
      connectWs(user.user_id)
    }
    return () => disconnectWs()
  }, [user?.user_id, fetchNotifications, connectWs, disconnectWs])

  useEffect(() => {
    if (!notifOpen) return
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setNotifOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [notifOpen])

  useEffect(() => {
    if (!menuOpen) return
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [menuOpen])

  function formatTimestamp(ts: string) {
    try {
      const d = new Date(ts)
      const now = new Date()
      const diff = now.getTime() - d.getTime()
      const mins = Math.floor(diff / 60000)
      if (mins < 1) return 'Just now'
      if (mins < 60) return `${mins}m ago`
      const hours = Math.floor(mins / 60)
      if (hours < 24) return `${hours}h ago`
      return d.toLocaleDateString()
    } catch {
      return ''
    }
  }

  return (
    <header className="flex items-center gap-4 h-[72px] px-6 lg:px-8 border-b border-border bg-background">
      <button
        onClick={onMenuClick}
        className="p-2 rounded-xl hover:bg-surface-variant transition-colors lg:hidden shrink-0"
        aria-label="Toggle sidebar"
      >
        <Sparkles className="w-5 h-5 text-text-muted" />
      </button>

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            className="p-2.5 rounded-xl hover:bg-surface-variant transition-colors relative cursor-pointer"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5 text-text-muted" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center bg-error text-[10px] font-bold text-white rounded-full px-1 ring-2 ring-background">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 top-full mt-2 w-[380px] rounded-2xl bg-surface border border-border shadow-xl shadow-black/20 overflow-hidden z-50 animate-fade-in">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <h3 className="text-sm font-semibold text-text">Notifications</h3>
                {unreadCount > 0 && (
                  <button
                    onClick={() => { markAllRead() }}
                    className="flex items-center gap-1 text-xs text-primary hover:text-primary-hover transition-colors cursor-pointer"
                  >
                    <CheckCheck className="w-3.5 h-3.5" />
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-[360px] overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-10 text-text-muted">
                    <Bell className="w-8 h-8 mb-2 opacity-40" />
                    <p className="text-sm">No notifications yet</p>
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={cn(
                        'px-4 py-3 border-b border-border last:border-0 hover:bg-surface-variant transition-colors',
                        !n.read && 'bg-primary/[0.03]'
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <div className={cn(
                          'w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5',
                          n.type === 'meal_plan_ready' ? 'bg-primary/10' : 'bg-warning/10'
                        )}>
                          {n.type === 'meal_plan_ready' ? (
                            <CheckCheck className="w-4 h-4 text-primary" />
                          ) : (
                            <Clock className="w-4 h-4 text-warning" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-sm font-medium text-text truncate">{n.title}</p>
                            <span className="text-[11px] text-text-muted shrink-0">{formatTimestamp(n.created_at)}</span>
                          </div>
                          <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">{n.message}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-surface-variant transition-colors cursor-pointer"
            aria-label="User menu"
          >
            <div className="w-9 h-9 rounded-xl bg-surface-variant border border-border flex items-center justify-center">
              <UserIcon className="w-4 h-4 text-text-muted" />
            </div>
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-2 w-56 rounded-2xl bg-surface border border-border shadow-xl shadow-black/20 overflow-hidden z-50 animate-fade-in">
              <div className="px-4 py-3.5 border-b border-border">
                <p className="text-sm font-medium text-text truncate">{user?.email || 'User'}</p>
                <p className="text-xs text-text-muted mt-0.5">Signed in</p>
              </div>
              <button
                onClick={() => { logout(); setMenuOpen(false) }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-text-secondary hover:bg-surface-variant transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
