import { create } from 'zustand'
import { markAllNotificationsRead } from '@/lib/api'

export interface AppNotification {
  id: string
  user_id: string
  type: string
  title: string
  message: string
  read: boolean
  created_at: string
}

interface NotificationState {
  notifications: AppNotification[]
  unreadCount: number
  connected: boolean
  socket: WebSocket | null
  addNotification: (n: AppNotification) => void
  setNotifications: (notifications: AppNotification[]) => void
  setUnreadCount: (count: number) => void
  markAllRead: () => Promise<void>
  connect: (userId: string) => void
  disconnect: () => void
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  connected: false,
  socket: null,

  addNotification: (n) => {
    set((s) => ({
      notifications: [n, ...s.notifications],
      unreadCount: s.unreadCount + 1,
    }))
  },

  setNotifications: (notifications) => set({ notifications }),

  setUnreadCount: (count) => set({ unreadCount: count }),

  markAllRead: async () => {
    const state = get()
    const userId = state.notifications[0]?.user_id
    if (!userId) return
    await markAllNotificationsRead(userId)
    set((s) => ({
      unreadCount: 0,
      notifications: s.notifications.map((n) => ({ ...n, read: true })),
    }))
  },

  connect: (userId) => {
    const existing = get().socket
    if (existing) {
      existing.close()
    }

    const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const wsUrl = BASE_URL.replace(/^http/, 'ws') + `/api/ws/${userId}`
    let socket: WebSocket

    try {
      socket = new WebSocket(wsUrl)
    } catch {
      return
    }

    socket.onopen = () => {
      set({ connected: true, socket })
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'notification' && data.notification) {
          get().addNotification(data.notification)
        }
      } catch {
        // ignore malformed messages
      }
    }

    socket.onclose = () => {
      set({ connected: false, socket: null })
    }

    socket.onerror = () => {
      socket.close()
    }
  },

  disconnect: () => {
    const socket = get().socket
    if (socket) {
      socket.close()
    }
    set({ connected: false, socket: null })
  },
}))
