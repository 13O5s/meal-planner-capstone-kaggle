import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChefHat, RotateCcw, MoreHorizontal, Trash2, Copy, BarChart3 } from 'lucide-react'
import type { MealData } from '@/lib/api'
import { NutritionBadge } from './NutritionBadge'
import { cn } from '@/lib/utils'

interface MealCardProps {
  meal: MealData
  mealIndex: number
  dayIndex: number
  onViewRecipe: (meal: MealData) => void
  onReplaceMeal: (dayIndex: number, mealIndex: number) => void
  isReplacing: boolean
}

const mealEmojis: Record<string, string> = {
  Breakfast: '\u{1F305}',
  Lunch: '\u2600\uFE0F',
  Dinner: '\u{1F319}',
  Snack: '\u{1F34E}',
}

const mealDotColors: Record<string, string> = {
  Breakfast: 'bg-orange-500',
  Lunch: 'bg-blue-500',
  Dinner: 'bg-purple-500',
  Snack: 'bg-primary',
}

export function MealCard({ meal, mealIndex, dayIndex, onViewRecipe, onReplaceMeal, isReplacing }: MealCardProps) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: mealIndex * 0.04 }}
      className="group relative rounded-xl bg-surface border border-border transition-all duration-200 hover:border-zinc-700/50 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-0.5"
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={cn(
            'w-9 h-9 rounded-lg flex items-center justify-center text-base shrink-0 ring-1 ring-white/[0.04]',
            meal.type === 'Breakfast' && 'bg-gradient-to-br from-orange-500/20 to-amber-500/10',
            meal.type === 'Lunch' && 'bg-gradient-to-br from-blue-500/20 to-sky-500/10',
            meal.type === 'Dinner' && 'bg-gradient-to-br from-purple-500/20 to-violet-500/10',
            meal.type === 'Snack' && 'bg-gradient-to-br from-primary/20 to-green-500/10',
          )}>
            {mealEmojis[meal.type] || '\u{1F37D}'}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-text-muted">{meal.type}</span>
            </div>
            <h3 className="text-sm font-semibold text-text leading-tight truncate max-w-md">{meal.name}</h3>
            <div className="flex flex-wrap gap-1 mt-1.5">
              {meal.calories != null && <NutritionBadge icon="🔥" value={`${meal.calories}`} color="calories" />}
              {meal.protein != null && <NutritionBadge icon="💪" value={`${meal.protein}g`} color="protein" />}
              {meal.carbs != null && <NutritionBadge icon="🌾" value={`${meal.carbs}g`} color="carbs" />}
              {meal.fat != null && <NutritionBadge icon="🥑" value={`${meal.fat}g`} color="fat" />}
              {meal.time && <NutritionBadge icon="⏱" value={meal.time} color="time" />}
              {meal.cost != null && <NutritionBadge icon="💰" value={`$${meal.cost.toFixed(2)}`} color="cost" />}
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={() => onViewRecipe(meal)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-[11px] font-medium hover:bg-primary/20 transition-all duration-200"
            >
              <ChefHat className="w-3 h-3" />
              Recipe
            </button>
            <button
              onClick={() => onReplaceMeal(dayIndex, mealIndex)}
              disabled={isReplacing}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-surface-variant text-text-muted text-[11px] font-medium hover:bg-surface-hover hover:text-text-secondary transition-all duration-200 disabled:opacity-40"
            >
              <RotateCcw className="w-3 h-3" />
              Replace
            </button>
            <div className="relative opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="p-1.5 rounded-lg hover:bg-surface-variant text-text-muted hover:text-text-secondary transition-colors"
              >
                <MoreHorizontal className="w-3.5 h-3.5" />
              </button>
              <AnimatePresence>
                {menuOpen && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -4 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -4 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-full mt-1 w-44 rounded-xl bg-surface border border-border shadow-xl shadow-black/30 overflow-hidden z-50"
                  >
                    {[
                      { icon: Copy, label: 'Duplicate', color: '' },
                      { icon: RotateCcw, label: 'Replace', color: '', action: () => onReplaceMeal(dayIndex, mealIndex) },
                      { icon: BarChart3, label: 'Nutrition', color: '', action: () => onViewRecipe(meal) },
                      { icon: Trash2, label: 'Delete', color: 'text-error', danger: true },
                    ].map((item, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setMenuOpen(false)
                          item.action?.()
                        }}
                        className={cn(
                          'w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
                          item.danger ? 'text-error hover:bg-error/10' : 'text-text-secondary hover:bg-surface-variant'
                        )}
                      >
                        <item.icon className="w-4 h-4" />
                        {item.label}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export { mealDotColors }
