import { motion } from 'framer-motion'
import { RotateCcw, Loader2, CalendarDays } from 'lucide-react'
import type { DayPlan, MealData } from '@/lib/api'
import { MealCard } from './MealCard'
import { cn } from '@/lib/utils'

interface MealDayCardProps {
  day: DayPlan
  dayIndex: number
  dayHeader: string
  expanded: boolean
  onToggle: () => void
  onRegenerateDay: (dayIndex: number) => void
  onReplaceMeal: (dayIndex: number, mealIndex: number) => void
  onViewRecipe: (meal: MealData) => void
  regeneratingDay: number | null
  replacingMeal: { dayIndex: number; mealIndex: number } | null
}

const dotColors: Record<string, string> = {
  Breakfast: 'bg-orange-500',
  Lunch: 'bg-blue-500',
  Dinner: 'bg-purple-500',
  Snack: 'bg-primary',
}

export function MealDayCard({
  day, dayIndex, dayHeader, onRegenerateDay, onReplaceMeal, onViewRecipe,
  regeneratingDay, replacingMeal,
}: MealDayCardProps) {
  const isReplacing = (mi: number) =>
    replacingMeal?.dayIndex === dayIndex && replacingMeal?.mealIndex === mi

  const [dayName, dateStr] = dayHeader.includes(',')
    ? [dayHeader.split(',')[0], dayHeader.split(', ')[1]]
    : [dayHeader, '']

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: dayIndex * 0.06 }}
    >
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
            <CalendarDays className="w-4 h-4 text-primary" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-text">{dayName}</h3>
            {dateStr && <p className="text-xs text-text-muted">{dateStr}</p>}
          </div>
        </div>
        <button
          onClick={() => onRegenerateDay(dayIndex)}
          disabled={regeneratingDay !== null}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-variant text-text-muted text-xs font-medium hover:bg-surface-hover hover:text-text-secondary transition-all duration-200 disabled:opacity-40"
        >
          {regeneratingDay === dayIndex ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <RotateCcw className="w-3.5 h-3.5" />
          )}
          Regenerate
        </button>
      </div>

      <div className="relative">
        {day.meals.map((meal, mi) => (
          <div key={`${meal.type}-${mi}`} className="flex gap-4">
            <div className="flex flex-col items-center w-4 shrink-0 pt-3">
              <div className={cn(
                'w-3 h-3 rounded-full ring-[3px] ring-background z-10',
                dotColors[meal.type] || 'bg-primary'
              )} />
              {mi < day.meals.length - 1 && (
                <div className="w-0.5 flex-1 min-h-[16px] bg-border" />
              )}
            </div>
            <div className={cn(
              'flex-1 min-w-0',
              mi < day.meals.length - 1 ? 'pb-5' : 'pb-0'
            )}>
              <MealCard
                meal={meal}
                mealIndex={mi}
                dayIndex={dayIndex}
                onViewRecipe={onViewRecipe}
                onReplaceMeal={onReplaceMeal}
                isReplacing={isReplacing(mi)}
              />
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
