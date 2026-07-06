import { X, ClipboardList, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { HistoryEntry } from '@/types'

interface HistoryViewModalProps {
  entry: HistoryEntry
  onClose: () => void
}

export function HistoryViewModal({ entry, onClose }: HistoryViewModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-12 pb-8 bg-black/50 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-surface dark:bg-surface-dark rounded-2xl shadow-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-outline-variant dark:border-outline-variant-dark">
          <div className="min-w-0 flex-1">
            <h2 className="text-h3 font-heading font-bold truncate">{entry.title}</h2>
            <p className="text-sm text-outline dark:text-outline-dark">
              {entry.created_at}
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="p-5 max-h-[70vh] overflow-y-auto space-y-4">
          {entry.type === 'meal_plan' && <MealPlanView data={entry.data as Record<string, unknown>} />}
          {entry.type === 'shopping_list' && <ShoppingListView data={entry.data as Record<string, unknown>} />}
        </div>
      </div>
    </div>
  )
}

function MealPlanView({ data }: { data: Record<string, unknown> }) {
  const days = data.days as Array<Record<string, unknown>> | undefined
  if (!days || days.length === 0) {
    return <p className="text-sm text-outline dark:text-outline-dark text-center py-8">No meal data available.</p>
  }
  return (
    <div className="space-y-4">
      {days.map((d, i) => {
        const dayLabel = d.day as string | undefined
        const meals = d.meals as Array<Record<string, unknown>> | undefined
        return (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <ClipboardList className="w-4 h-4 text-primary dark:text-primary-dark" />
                <p className="text-sm font-semibold">{dayLabel || `Day ${i + 1}`}</p>
              </div>
              {meals && meals.length > 0 ? (
                <div className="space-y-2">
                  {meals.map((meal, j) => {
                    const name = meal.name as string
                    const calories = meal.calories as number | undefined
                    const protein = meal.protein as number | undefined
                    const carbs = meal.carbs as number | undefined
                    const fat = meal.fat as number | undefined
                    const time = meal.time as string | undefined
                    const cost = meal.cost as number | undefined
                    return (
                      <div key={j} className="flex items-start gap-3 text-sm">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary dark:bg-primary-dark shrink-0 mt-1.5" />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">{name}</p>
                          <p className="text-xs text-outline dark:text-outline-dark">
                            {calories ? `${calories} cal` : ''}
                            {calories && (protein || carbs || fat) ? ' · ' : ''}
                            {protein ? `P:${protein}g` : ''}
                            {protein && (carbs || fat) ? ' · ' : ''}
                            {carbs ? `C:${carbs}g` : ''}
                            {carbs && fat ? ' · ' : ''}
                            {fat ? `F:${fat}g` : ''}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {time && (
                            <span className="text-xs text-outline dark:text-outline-dark">{time}</span>
                          )}
                          {cost !== undefined && (
                            <span className="text-xs font-medium text-secondary dark:text-secondary-dark">
                              ${cost.toFixed(2)}
                            </span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-xs text-outline dark:text-outline-dark">No meals for this day.</p>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

function ShoppingListView({ data }: { data: Record<string, unknown> }) {
  const purchased = data.purchased_items as Array<{
    id: string
    ingredient_name: string
    total_quantity: number
    unit: string
    estimated_cost: number
    category: string
  }> | undefined
  if (!purchased || purchased.length === 0) {
    return <p className="text-sm text-outline dark:text-outline-dark text-center py-8">No purchased items.</p>
  }
  return (
    <div className="space-y-2">
      {purchased.map((item) => (
        <div
          key={item.id}
          className="flex items-center gap-3 p-3 rounded-xl bg-surface-container-low dark:bg-surface-container-low-dark"
        >
          <div className="w-8 h-8 rounded-lg bg-secondary/10 text-secondary dark:text-secondary-dark flex items-center justify-center shrink-0">
            <Check className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{item.ingredient_name}</p>
            <p className="text-xs text-outline dark:text-outline-dark">{item.total_quantity} {item.unit}</p>
          </div>
          <span className="text-sm font-medium text-secondary dark:text-secondary-dark shrink-0">
            ${item.estimated_cost.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  )
}
