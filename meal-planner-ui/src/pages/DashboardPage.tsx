import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Target, Flame, UtensilsCrossed, ShoppingCart, ArrowRight, Check, BookOpen, CalendarDays, Sparkles, Package } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useAuthStore } from '@/stores/auth-store'
import { getSessionState, getMealPlans, getUserProfile, generateRecipeDetail, getShoppingList, resolveMealIngredients, updateSessionState } from '@/lib/api'
import { RecipeDetailModal } from '@/components/RecipeDetailModal'
import { NutritionBadge } from '@/components/meal-plans/NutritionBadge'
import type { RecipeDetail } from '@/lib/api'

const EATEN_STORAGE_KEY = 'dashboard_eaten_meals'
const INVENTORY_STORAGE_KEY = 'meal_planner_inventory'

interface DashboardInventoryItem {
  id: string
  name: string
  quantity: number
  unit: string
  category: string
}

function loadInventory(): DashboardInventoryItem[] {
  try {
    const raw = localStorage.getItem(INVENTORY_STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function saveInventory(items: DashboardInventoryItem[]) {
  localStorage.setItem(INVENTORY_STORAGE_KEY, JSON.stringify(items))
}

function getTodayDateString(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function diffDays(start: string, end: string): number {
  const s = new Date(start + 'T00:00:00')
  const e = new Date(end + 'T00:00:00')
  return Math.round((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24))
}

function loadEatenMeals(): Set<string> {
  try {
    const raw = localStorage.getItem(EATEN_STORAGE_KEY)
    if (raw) return new Set(JSON.parse(raw))
  } catch { /* ignore */ }
  return new Set()
}

function saveEatenMeals(set: Set<string>): void {
  localStorage.setItem(EATEN_STORAGE_KEY, JSON.stringify([...set]))
}

function formatDisplayDate(): string {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function getMealIcon(time: string): string {
  const t = time.toLowerCase()
  if (t.includes('breakfast')) return '\u{1F305}'
  if (t.includes('lunch')) return '\u2600\uFE0F'
  if (t.includes('dinner')) return '\u{1F319}'
  return '\u{1F37D}'
}

export function DashboardPage() {
  const navigate = useNavigate()
  const lastSessionId = useWorkflowStore((s) => s.lastSessionId)
  const userId = useAuthStore((s) => s.user?.user_id) || ''
  const [loading, setLoading] = useState(true)
  const [goal, setGoal] = useState('Not set')
  const [calorieTarget, setCalorieTarget] = useState(2000)
  const [mealsPerDay, setMealsPerDay] = useState(3)
  const [meals, setMeals] = useState<Array<{ time: string; name: string; calories: number; protein: number; carbs?: number; fat?: number; cost?: number }>>([])
  const [shoppingNeeded, setShoppingNeeded] = useState<number | null>(null)
  const [hasShoppingList, setHasShoppingList] = useState(false)
  const [eatenMeals, setEatenMeals] = useState<Set<string>>(() => loadEatenMeals())

  const [recipeMeal, setRecipeMeal] = useState<{ name: string; type: string } | null>(null)
  const [recipeDetail, setRecipeDetail] = useState<RecipeDetail | null>(null)
  const [recipeLoading, setRecipeLoading] = useState(false)
  const [recipeError, setRecipeError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)

      const todayDate = getTodayDateString()

      const results = await Promise.all([
        lastSessionId ? getSessionState(lastSessionId).catch(() => ({} as Record<string, unknown>)) : Promise.resolve({} as Record<string, unknown>),
        userId ? getUserProfile(userId).catch(() => null) : Promise.resolve(null),
        userId ? getMealPlans(userId).catch(() => null) : Promise.resolve(null),
        userId ? getShoppingList(userId).catch(() => null) : Promise.resolve(null),
      ])
      if (cancelled) return

      const [session, dbProfile, planResult, shoppingResult] = results

      const pGoal = dbProfile?.goal as string | undefined
      const pCalTarget = dbProfile?.daily_calorie_target as number | undefined
      const pMealsPerDay = dbProfile?.meals_per_day as number | undefined

      setGoal(pGoal || 'Not set')
      setCalorieTarget(pCalTarget || 2000)
      setMealsPerDay(pMealsPerDay || 3)

      let shoppingItems: Array<Record<string, unknown>> = []

      const sessionShopping = (session.shopping_list as Record<string, unknown>) || {}
      const sessionItems = (sessionShopping.items as Array<Record<string, unknown>>) || []

      if (sessionItems.length > 0) {
        shoppingItems = sessionItems
      } else if (shoppingResult?.success && shoppingResult.shopping_list?.items) {
        shoppingItems = shoppingResult.shopping_list.items as unknown as Array<Record<string, unknown>>
      }

      if (shoppingItems.length > 0) {
        setHasShoppingList(true)
        const hasPurchasedField = shoppingItems.some((item) => item.purchased !== undefined)
        const needed = hasPurchasedField
          ? shoppingItems.filter((item) => !item.purchased).length
          : shoppingItems.length
        setShoppingNeeded(needed)
      } else {
        setHasShoppingList(false)
        setShoppingNeeded(null)
      }

      let todayMeals: Array<{ time: string; name: string; calories: number; protein: number }> = []

      if (planResult?.success && planResult.plans?.length > 0) {
        const plan = planResult.plans[0]
        let dayIndex = -1
        if (plan.start_date) {
          dayIndex = diffDays(plan.start_date, todayDate)
        }
        if (dayIndex >= 0 && dayIndex < plan.days.length) {
          todayMeals = plan.days[dayIndex].meals.map((m) => ({
            time: m.type || '',
            name: m.name || '',
            calories: m.calories || 0,
            protein: m.protein || 0,
            carbs: m.carbs,
            fat: m.fat,
            cost: m.cost,
          }))
        }
        if (todayMeals.length === 0) {
          const todayName = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][new Date().getDay()]
          const matchingDay = plan.days.find((d) => {
            const dayLabel = (d.day || '').trim().toLowerCase()
            return dayLabel === todayDate || dayLabel === todayName.toLowerCase()
          })
          if (matchingDay) {
            todayMeals = matchingDay.meals.map((m) => ({
              time: m.type || '',
              name: m.name || '',
              calories: m.calories || 0,
              protein: m.protein || 0,
              carbs: m.carbs,
              fat: m.fat,
              cost: m.cost,
            }))
          }
        }
      }

      if (todayMeals.length === 0) {
        const mealPlanFromSession = (session.meal_plan as Array<Record<string, unknown>>) || []
        const todayName = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][new Date().getDay()]
        const sessionEntry = mealPlanFromSession.find((d: Record<string, unknown>) => {
          const day = ((d.day as string) || '').trim()
          return day === todayDate || day.toLowerCase() === todayName.toLowerCase()
        })
        if (sessionEntry) {
          todayMeals = ((sessionEntry.meals as Array<Record<string, unknown>>) || []).map((m: Record<string, unknown>) => ({
            time: (m.type as string) || (m.meal as string) || '',
            name: (m.recipe as string) || (m.name as string) || '',
            calories: (m.calories as number) || 0,
            protein: (m.protein as number) || 0,
            carbs: m.carbs as number | undefined,
            fat: m.fat as number | undefined,
            cost: m.cost as number | undefined,
          }))
        }
      }

      setMeals(todayMeals)
      setLoading(false)
    }
    load()
    return () => { cancelled = true }
  }, [lastSessionId, userId])

  useEffect(() => {
    saveEatenMeals(eatenMeals)
  }, [eatenMeals])

  const toggleEaten = useCallback(async (time: string, name: string) => {
    const key = `${time}|${name}`
    const wasEaten = eatenMeals.has(key)

    setEatenMeals(prev => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })

    try {
      const res = await resolveMealIngredients(name, time)
      if (!res.success || res.ingredients.length === 0) return
      const inventory = loadInventory()
      for (const ing of res.ingredients) {
        const match = inventory.find(
          (i) => i.name.toLowerCase().trim() === ing.name.toLowerCase().trim() && i.unit === ing.unit
        )
        if (!match) continue
        if (wasEaten) {
          match.quantity += ing.quantity
        } else {
          match.quantity -= ing.quantity
        }
      }
      const updated = inventory.filter((i) => i.quantity > 0)
      saveInventory(updated)
      if (lastSessionId) {
        await updateSessionState(lastSessionId, {
          available_ingredients: updated.map((i) => ({
            name: i.name,
            quantity: i.quantity,
            unit: i.unit,
            original_text: i.name,
            category: i.category,
          })),
        }).catch(() => {})
      }
    } catch {
      // Silently fail — don't block the eat toggle
    }
  }, [eatenMeals, lastSessionId])

  const isEaten = useCallback((time: string, name: string) => {
    return eatenMeals.has(`${time}|${name}`)
  }, [eatenMeals])

  const eatenCount = meals.filter(m => isEaten(m.time, m.name)).length
  const calorieCurrentFromEaten = meals
    .filter(m => isEaten(m.time, m.name))
    .reduce((sum, m) => sum + m.calories, 0)

  const handleViewRecipe = async (time: string, name: string) => {
    setRecipeMeal({ name, type: time })
    setRecipeDetail(null)
    setRecipeError(null)
    setRecipeLoading(true)
    try {
      const res = await generateRecipeDetail(name, time, 'Balanced')
      if (res.success && res.recipe) {
        setRecipeDetail(res.recipe)
      } else {
        setRecipeError(res.error || 'Could not load recipe details')
      }
    } catch {
      setRecipeError('Network error while fetching recipe')
    }
    setRecipeLoading(false)
  }

  const handleCloseRecipe = () => {
    setRecipeMeal(null)
    setRecipeDetail(null)
    setRecipeError(null)
  }

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="h-9 w-48 rounded-lg bg-surface animate-shimmer" />
            <div className="h-5 w-72 rounded bg-surface animate-shimmer mt-2" />
          </div>
          <div className="h-5 w-56 rounded bg-surface animate-shimmer hidden sm:block" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-6 rounded-2xl bg-surface border border-border animate-shimmer">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-background" />
                <div className="h-3 w-24 rounded bg-background" />
              </div>
              <div className="h-8 w-32 rounded bg-background" />
              <div className="h-4 w-20 rounded bg-background mt-3" />
            </div>
          ))}
        </div>
        <div>
          <div className="h-5 w-36 rounded bg-surface animate-shimmer mb-4" />
          <div className="flex gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 w-48 rounded-xl bg-surface animate-shimmer" />
            ))}
          </div>
        </div>
        <div className="p-6 rounded-2xl bg-surface border border-border animate-shimmer">
          <div className="h-6 w-48 rounded bg-background" />
          <div className="space-y-4 mt-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-xl bg-background" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  let shoppingValue: string
  if (!hasShoppingList) {
    shoppingValue = 'No List'
  } else if (shoppingNeeded === 0) {
    shoppingValue = 'All purchased'
  } else {
    shoppingValue = `${shoppingNeeded} to buy`
  }

  const caloriePercentage = calorieTarget > 0
    ? Math.min(Math.round((calorieCurrentFromEaten / calorieTarget) * 100), 100)
    : 0

  const statCards = [
    {
      icon: Target,
      label: 'Current Goal',
      value: goal,
      description: 'Current nutrition strategy',
      iconColor: 'text-primary',
      iconBg: 'bg-primary/10',
      progress: undefined as number | undefined,
    },
    {
      icon: Flame,
      label: 'Daily Calories',
      value: meals.length > 0
        ? `${calorieCurrentFromEaten.toLocaleString()} / ${calorieTarget.toLocaleString()} kcal`
        : `${calorieTarget.toLocaleString()} kcal target`,
      description: `${caloriePercentage}% of target`,
      iconColor: 'text-warning',
      iconBg: 'bg-warning/10',
      progress: calorieTarget > 0 ? Math.min(calorieCurrentFromEaten / calorieTarget, 1) : 0,
    },
    {
      icon: UtensilsCrossed,
      label: 'Meals Planned',
      value: `${eatenCount} / ${mealsPerDay} Meals`,
      description: meals.length === 0 ? 'No meals planned'
        : eatenCount === 0 ? 'No meals tracked'
        : eatenCount === meals.length ? 'All meals completed'
        : `${eatenCount} of ${meals.length} eaten`,
      iconColor: 'text-blue',
      iconBg: 'bg-blue/10',
      progress: undefined as number | undefined,
    },
    {
      icon: ShoppingCart,
      label: 'Shopping List',
      value: shoppingValue,
      description: !hasShoppingList ? 'Start shopping planning'
        : shoppingNeeded === 0 ? 'Everything bought'
        : `${shoppingNeeded} remaining`,
      iconColor: 'text-purple',
      iconBg: 'bg-purple/10',
      progress: undefined as number | undefined,
    },
  ]

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-text tracking-tight">Dashboard</h1>
          <p className="text-sm text-text-secondary mt-1.5">Welcome back. Here's your meal planning overview for today.</p>
        </div>
        <div className="hidden sm:flex items-center gap-2 text-text-muted">
          <CalendarDays className="w-4 h-4" />
          <span className="text-sm">{formatDisplayDate()}</span>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card) => (
          <div
            key={card.label}
            className="p-6 rounded-2xl bg-surface border border-border shadow-sm hover:-translate-y-1 hover:shadow-xl transition-all duration-200 group"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-xl ${card.iconBg} flex items-center justify-center`}>
                <card.icon className={`w-5 h-5 ${card.iconColor}`} />
              </div>
              <span className="text-xs font-medium text-text-muted uppercase tracking-wider">{card.label}</span>
            </div>
            <p className="text-3xl font-bold text-text">{card.value}</p>
            <p className="text-sm text-text-secondary mt-1.5">{card.description}</p>
            {card.progress !== undefined && (
              <div className="mt-3 h-1 bg-secondary/20 rounded-full overflow-hidden">
                <div
                  className="h-full bg-warning rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${Math.min(card.progress * 100, 100)}%` }}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-text">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Button
            variant="primary"
            size="lg"
            className="h-12 rounded-xl bg-gradient-to-r from-primary to-emerald-400 hover:scale-[1.02] transition-all duration-200 shadow-md shadow-primary/20"
            onClick={() => navigate('/meal-plans')}
          >
            <Sparkles className="w-4 h-4" />
            Generate Meal Plan
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="h-12 rounded-xl hover:scale-[1.02] transition-all duration-200"
            onClick={() => navigate('/inventory')}
          >
            <Package className="w-4 h-4" />
            Update Inventory
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="h-12 rounded-xl hover:scale-[1.02] transition-all duration-200"
            onClick={() => navigate('/shopping-lists')}
          >
            <ShoppingCart className="w-4 h-4" />
            Shopping List
          </Button>
        </div>
      </div>

      {/* Today's Meals */}
      <div className="p-6 rounded-2xl bg-surface border border-border">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-text">Today's Meals</h2>
          {meals.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="text-text-muted hover:text-text"
              onClick={() => navigate('/meal-plans')}
            >
              View Full Plan
              <ArrowRight className="w-4 h-4" />
            </Button>
          )}
        </div>

        {meals.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-center">
            <span className="text-5xl mb-4">{'\u{1F37D}'}</span>
            <h3 className="text-xl font-semibold text-text mb-2">No meal plan for today</h3>
            <p className="text-sm text-text-secondary max-w-md mb-6">
              Generate a personalized meal plan based on your profile and inventory.
            </p>
            <Button
              variant="primary"
              size="lg"
              className="h-12 rounded-xl bg-gradient-to-r from-primary to-emerald-400 shadow-md shadow-primary/20"
              onClick={() => navigate('/meal-plans')}
            >
              <Sparkles className="w-4 h-4" />
              Generate Meal Plan
            </Button>
          </div>
        ) : (
          <div className="space-y-0">
            {meals.map((meal, i) => {
              const eaten = isEaten(meal.time, meal.name)
              const dotColor = meal.time.toLowerCase().includes('breakfast') ? 'bg-orange-500'
                : meal.time.toLowerCase().includes('lunch') ? 'bg-blue-500'
                : meal.time.toLowerCase().includes('dinner') ? 'bg-purple-500'
                : 'bg-primary'
              return (
                <div key={i} className="flex gap-4">
                  <div className="flex flex-col items-center w-4 shrink-0 pt-3">
                    <div className={`w-3 h-3 rounded-full ring-[3px] ring-background z-10 transition-colors duration-200 ${eaten ? 'bg-primary' : dotColor}`} />
                    {i < meals.length - 1 && (
                      <div className="w-0.5 flex-1 min-h-[16px] bg-border" />
                    )}
                  </div>
                  <div className={`flex-1 min-w-0 ${i < meals.length - 1 ? 'pb-5' : 'pb-0'}`}>
                    <div className={`rounded-xl border transition-all duration-200 ${
                      eaten
                        ? 'bg-primary/5 border-primary/20'
                        : 'bg-surface border-border hover:border-zinc-700/50 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-0.5'
                    }`}>
                      <div className="p-4">
                        <div className="flex items-start gap-3">
                          <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-base shrink-0 ring-1 ring-white/[0.04] ${
                            eaten
                              ? 'bg-primary/10'
                              : meal.time.toLowerCase().includes('breakfast') ? 'bg-gradient-to-br from-orange-500/20 to-amber-500/10'
                              : meal.time.toLowerCase().includes('lunch') ? 'bg-gradient-to-br from-blue-500/20 to-sky-500/10'
                              : meal.time.toLowerCase().includes('dinner') ? 'bg-gradient-to-br from-purple-500/20 to-violet-500/10'
                              : 'bg-gradient-to-br from-primary/20 to-green-500/10'
                          }`}>
                            {getMealIcon(meal.time)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-[10px] font-semibold uppercase tracking-widest ${eaten ? 'text-primary' : 'text-text-muted'}`}>
                              {meal.time}
                            </p>
                            <p className={`text-sm font-semibold leading-tight truncate max-w-md mt-0.5 ${eaten ? 'text-text line-through opacity-60' : 'text-text'}`}>
                              {meal.name}
                            </p>
                            <div className="flex flex-wrap gap-1.5 mt-2">
                              <NutritionBadge icon="🔥" value={`${meal.calories}`} color="calories" />
                              <NutritionBadge icon="💪" value={`${meal.protein}g`} color="protein" />
                              {meal.carbs != null && <NutritionBadge icon="🌾" value={`${meal.carbs}g`} color="carbs" />}
                              {meal.fat != null && <NutritionBadge icon="🥑" value={`${meal.fat}g`} color="fat" />}
                              {meal.cost != null && <NutritionBadge icon="💰" value={`$${meal.cost.toFixed(2)}`} color="cost" />}
                            </div>
                          </div>
                          <div className="flex items-center gap-1.5 shrink-0 self-center">
                            <button
                              onClick={() => handleViewRecipe(meal.time, meal.name)}
                              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-all duration-200"
                            >
                              <BookOpen className="w-4 h-4" />
                              Recipe
                            </button>
                            <button
                              onClick={() => toggleEaten(meal.time, meal.name)}
                              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all duration-200 ${
                                eaten
                                  ? 'bg-primary text-white shadow-sm'
                                  : 'bg-surface-variant text-text-muted hover:bg-surface-hover hover:text-text-secondary'
                              }`}
                            >
                              <Check className="w-3 h-3" />
                              {eaten ? 'Eaten' : 'Mark Eaten'}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {recipeMeal && (
        <RecipeDetailModal
          mealName={recipeMeal.name}
          mealType={recipeMeal.type}
          strategy="Balanced"
          detail={recipeDetail}
          loading={recipeLoading}
          error={recipeError}
          onClose={handleCloseRecipe}
        />
      )}
    </div>
  )
}
