import { useState, useEffect, type ComponentType } from 'react'
import { History, ClipboardList, ShoppingCart, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/components/shared/EmptyState'
import { HistoryViewModal } from '@/components/HistoryViewModal'
import { getHistory } from '@/lib/api'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'
import type { HistoryEntry } from '@/types'

const filters = ['All', 'Meal Plans', 'Shopping Lists']

const typeConfig: Record<string, { icon: ComponentType<{ className?: string }>; label: string; color: string }> = {
  meal_plan: { icon: ClipboardList, label: 'Meal Plan', color: 'bg-primary/10 text-primary' },
  shopping_list: { icon: ShoppingCart, label: 'Shopping List', color: 'bg-blue/10 text-blue' },
}

export function HistoryPage() {
  const user = useAuthStore((s) => s.user)
  const userId = user?.user_id || ''

  const [loading, setLoading] = useState(true)
  const [entries, setEntries] = useState<HistoryEntry[]>([])
  const [activeFilter, setActiveFilter] = useState('All')
  const [viewEntry, setViewEntry] = useState<HistoryEntry | null>(null)

  useEffect(() => {
    if (!userId) { setLoading(false); return }
    getHistory(userId)
      .then((data) => { setEntries(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [userId])

  const filtered = entries.filter((e) => {
    if (activeFilter === 'All') return true
    if (activeFilter === 'Meal Plans') return e.type === 'meal_plan'
    if (activeFilter === 'Shopping Lists') return e.type === 'shopping_list'
    return true
  })

  if (loading) {
    return (
      <div className="p-6 lg:p-8 max-w-4xl mx-auto min-h-screen flex items-center justify-center">
        <p className="text-sm text-text-muted">Loading history...</p>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-4xl mx-auto animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-text">History</h1>
        <p className="text-text-secondary mt-1.5 text-sm">Your past meal plans and shopping lists.</p>
      </div>

      <div className="flex gap-1.5">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={cn(
              'px-4 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer',
              activeFilter === f
                ? 'bg-primary text-on-primary'
                : 'hover:bg-surface-variant text-text-muted hover:text-text'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<History className="w-8 h-8" />}
          title="No history yet"
          description="Your past meal plans and shopping lists will appear here after you generate them."
        />
      ) : (
        <div className="space-y-2">
          {filtered.map((entry) => {
            const config = typeConfig[entry.type]
            if (!config) return null
            return (
              <Card key={entry.id} variant="interactive" onClick={() => setViewEntry(entry)}>
                <CardContent className="p-5">
                  <div className="flex items-center gap-4">
                    <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center shrink-0', config.color)}>
                      <config.icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-text">{entry.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', config.color)}>{config.label}</span>
                        <span className="text-xs text-text-muted">{entry.created_at}</span>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-text-muted shrink-0" />
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {viewEntry && (
        <HistoryViewModal entry={viewEntry} onClose={() => setViewEntry(null)} />
      )}
    </div>
  )
}
