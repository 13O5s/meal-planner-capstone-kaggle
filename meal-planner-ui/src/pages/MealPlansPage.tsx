import { useState, useEffect, useCallback, useRef } from 'react'
import { ClipboardList, Wallet, Trash2, ArrowLeft, Loader2, AlertCircle, Heart, Dumbbell, TrendingDown, TrendingUp, Scale, Users, GraduationCap, Briefcase, CalendarDays, Sparkles, Clock3, Eye, ShoppingCart, UtensilsCrossed } from 'lucide-react'
import { getMealPlans, createMealPlan, deleteMealPlan, regenerateDay, replaceMeal, generateRecipeDetail, applyShoppingListFromPlan, generateMealPlan, getUserProfile } from '@/lib/api'
import type { MealPlan, DayPlan, MealData, RecipeDetail } from '@/lib/api'
import { RecipeDetailModal } from '@/components/RecipeDetailModal'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'
import { MealPlanHeader } from '@/components/meal-plans/MealPlanHeader'
import { MealStats } from '@/components/meal-plans/MealStats'
import { MealDayCard } from '@/components/meal-plans/MealDayCard'


const strategies = ['Budget', 'Healthy', 'High Protein', 'Weight Loss', 'Weight Gain', 'Balanced', 'Family', 'Student', 'Office Worker']

const strategyIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  'Budget': Wallet,
  'Healthy': Heart,
  'High Protein': Dumbbell,
  'Weight Loss': TrendingDown,
  'Weight Gain': TrendingUp,
  'Balanced': Scale,
  'Family': Users,
  'Student': GraduationCap,
  'Office Worker': Briefcase,
}

const strategyColors: Record<string, string> = {
  'Budget': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'Healthy': 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  'High Protein': 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  'Weight Loss': 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  'Weight Gain': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  'Balanced': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  'Family': 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  'Student': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  'Office Worker': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
}

const strategySelectedChips: Record<string, string> = {
  'Budget': 'bg-emerald-500/15 border-emerald-400/40 shadow-sm',
  'Healthy': 'bg-sky-500/15 border-sky-400/40 shadow-sm',
  'High Protein': 'bg-violet-500/15 border-violet-400/40 shadow-sm',
  'Weight Loss': 'bg-orange-500/15 border-orange-400/40 shadow-sm',
  'Weight Gain': 'bg-rose-500/15 border-rose-400/40 shadow-sm',
  'Balanced': 'bg-slate-500/15 border-slate-400/40 shadow-sm',
  'Family': 'bg-pink-500/15 border-pink-400/40 shadow-sm',
  'Student': 'bg-cyan-500/15 border-cyan-400/40 shadow-sm',
  'Office Worker': 'bg-indigo-500/15 border-indigo-400/40 shadow-sm',
}

const strategyIconColors: Record<string, string> = {
  'Budget': 'text-emerald-400',
  'Healthy': 'text-sky-400',
  'High Protein': 'text-violet-400',
  'Weight Loss': 'text-orange-400',
  'Weight Gain': 'text-rose-400',
  'Balanced': 'text-slate-400',
  'Family': 'text-pink-400',
  'Student': 'text-cyan-400',
  'Office Worker': 'text-indigo-400',
}

const strategyContainers: Record<string, string> = {
  'Budget': 'bg-emerald-500/10 text-emerald-400',
  'Healthy': 'bg-sky-500/10 text-sky-400',
  'High Protein': 'bg-violet-500/10 text-violet-400',
  'Weight Loss': 'bg-orange-500/10 text-orange-400',
  'Weight Gain': 'bg-rose-500/10 text-rose-400',
  'Balanced': 'bg-slate-500/10 text-slate-400',
  'Family': 'bg-pink-500/10 text-pink-400',
  'Student': 'bg-cyan-500/10 text-cyan-400',
  'Office Worker': 'bg-indigo-500/10 text-indigo-400',
}

const FALLBACK_DAYS: DayPlan[] = [
  {
    day: 'Monday',
    meals: [
      { type: 'Breakfast', name: 'Oatmeal with Banana & Honey', calories: 320, protein: 12, carbs: 52, fat: 6, time: '15 min', cost: 1.20 },
      { type: 'Lunch', name: 'Chicken & Vegetable Stir Fry', calories: 450, protein: 38, carbs: 25, fat: 16, time: '25 min', cost: 3.50 },
      { type: 'Dinner', name: 'Lentil Pasta with Marinara', calories: 580, protein: 25, carbs: 70, fat: 12, time: '30 min', cost: 2.80 },
    ],
  },
  {
    day: 'Tuesday',
    meals: [
      { type: 'Breakfast', name: 'Greek Yogurt & Granola', calories: 280, protein: 18, carbs: 38, fat: 5, time: '5 min', cost: 1.80 },
      { type: 'Lunch', name: 'Grilled Chicken Salad', calories: 400, protein: 35, carbs: 18, fat: 22, time: '15 min', cost: 4.00 },
      { type: 'Dinner', name: 'Baked Salmon with Vegetables', calories: 520, protein: 40, carbs: 20, fat: 28, time: '30 min', cost: 5.00 },
    ],
  },
  {
    day: 'Wednesday',
    meals: [
      { type: 'Breakfast', name: 'Smoothie Bowl', calories: 350, protein: 15, carbs: 55, fat: 8, time: '10 min', cost: 2.00 },
      { type: 'Lunch', name: 'Turkey Sandwich', calories: 380, protein: 30, carbs: 35, fat: 12, time: '10 min', cost: 3.00 },
      { type: 'Dinner', name: 'Vegetable Stir Fry with Tofu', calories: 450, protein: 20, carbs: 40, fat: 18, time: '20 min', cost: 3.50 },
    ],
  },
  {
    day: 'Thursday',
    meals: [
      { type: 'Breakfast', name: 'Scrambled Eggs with Toast', calories: 380, protein: 22, carbs: 28, fat: 18, time: '10 min', cost: 1.20 },
      { type: 'Lunch', name: 'Quinoa Buddha Bowl', calories: 420, protein: 18, carbs: 48, fat: 16, time: '20 min', cost: 3.50 },
      { type: 'Dinner', name: 'Beef Stir Fry', calories: 550, protein: 42, carbs: 30, fat: 24, time: '25 min', cost: 4.50 },
    ],
  },
  {
    day: 'Friday',
    meals: [
      { type: 'Breakfast', name: 'Protein Pancakes', calories: 340, protein: 25, carbs: 40, fat: 10, time: '15 min', cost: 1.80 },
      { type: 'Lunch', name: 'Tuna Salad Wrap', calories: 360, protein: 28, carbs: 30, fat: 14, time: '10 min', cost: 3.00 },
      { type: 'Dinner', name: 'Grilled Steak with Sweet Potato', calories: 600, protein: 45, carbs: 42, fat: 26, time: '30 min', cost: 6.00 },
    ],
  },
  {
    day: 'Saturday',
    meals: [
      { type: 'Breakfast', name: 'Avocado Toast & Eggs', calories: 380, protein: 22, carbs: 28, fat: 22, time: '12 min', cost: 2.50 },
      { type: 'Lunch', name: 'Minestrone Soup', calories: 300, protein: 12, carbs: 35, fat: 8, time: '25 min', cost: 2.50 },
      { type: 'Dinner', name: 'Chicken Curry with Rice', calories: 520, protein: 35, carbs: 48, fat: 18, time: '35 min', cost: 4.00 },
    ],
  },
  {
    day: 'Sunday',
    meals: [
      { type: 'Breakfast', name: 'French Toast', calories: 350, protein: 14, carbs: 42, fat: 16, time: '15 min', cost: 1.50 },
      { type: 'Lunch', name: 'Caprese Salad', calories: 320, protein: 16, carbs: 10, fat: 24, time: '10 min', cost: 3.00 },
      { type: 'Dinner', name: 'Roast Chicken with Vegetables', calories: 580, protein: 48, carbs: 35, fat: 22, time: '60 min', cost: 5.50 },
    ],
  },
]

const DAY_LABELS = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy']

function formatDateRange(start: string, days: number): string {
  const s = new Date(start + 'T00:00:00')
  const e = new Date(s)
  e.setDate(e.getDate() + days - 1)
  const fmt = (d: Date) =>
    `${DAY_LABELS[d.getDay()]}, ${d.getDate()}/${d.getMonth() + 1}`
  return days === 1 ? fmt(s) : `${fmt(s)} → ${fmt(e)}`
}

function getDayDate(start: string | undefined, index: number, fallbackLabel: string): string {
  if (!start) return fallbackLabel
  const d = new Date(start + 'T00:00:00')
  d.setDate(d.getDate() + index)
  return `${DAY_LABELS[d.getDay()]}, ${d.getDate()}/${d.getMonth() + 1}`
}

export function MealPlansPage() {
  const [view, setView] = useState<'list' | 'generating' | 'detail'>('list')
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [activePlan, setActivePlan] = useState<MealPlan | null>(null)
  const [strategy, setStrategy] = useState('Budget')
  const [numDays, setNumDays] = useState(7)
  const [startDate, setStartDate] = useState(() => new Date().toISOString().split('T')[0])
  const [_generatedDays, setGeneratedDays] = useState<DayPlan[] | null>(null)
  const [saving, setSaving] = useState(false)
  const [regeneratingDay, setRegeneratingDay] = useState<number | null>(null)
  const [replacingMeal, setReplacingMeal] = useState<{ dayIndex: number; mealIndex: number } | null>(null)
  const [recipeDetail, setRecipeDetail] = useState<RecipeDetail | null>(null)
  const [recipeLoading, setRecipeLoading] = useState(false)
  const [recipeMeal, setRecipeMeal] = useState<{ name: string; type: string } | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const recipeCacheRef = useRef<Record<string, RecipeDetail>>({})

  const user = useAuthStore((s) => s.user)
  const userId = user?.user_id || ''

  const loadPlans = useCallback(async () => {
    if (!userId) return
    try {
      const res = await getMealPlans(userId)
      if (res.success) setPlans(res.plans)
    } catch { /* ignore */ }
  }, [userId])

  useEffect(() => { loadPlans() }, [loadPlans])

  const handleGenerate = async () => {
    setGeneratedDays(null)
    setView('generating')
    setSaving(true)
    setErrorMessage(null)

    try {
      const profile = await getUserProfile(userId)
      const res = await generateMealPlan(userId, {
        strategy, numDays, startDate,
        userProfile: profile || undefined,
      })

      if (!res.success || !res.days?.length) {
        throw new Error(res.error || 'AI returned empty result')
      }

      const days = res.days.slice(0, numDays)
      setGeneratedDays(days)
      const saved = await createMealPlan(userId, { strategy, numDays, start_date: startDate, days })
      if (saved.success) {
        setActivePlan(saved.plan)
        await loadPlans()
      } else {
        setActivePlan({ id: 'local', strategy, numDays, start_date: startDate, days, created_at: new Date().toISOString() })
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setErrorMessage(msg)
      const days = FALLBACK_DAYS.slice(0, numDays)
      setGeneratedDays(days)
      setActivePlan({ id: 'local', strategy, numDays, start_date: startDate, days, created_at: new Date().toISOString() })
    }

    setSaving(false)
    setView('detail')
  }

  const handleGenerateOffline = async () => {
    setView('generating')
    setSaving(true)
    const days = FALLBACK_DAYS.slice(0, numDays)
    setGeneratedDays(days)
    try {
      const res = await createMealPlan(userId, { strategy, numDays, start_date: startDate, days })
      if (res.success) {
        setActivePlan(res.plan)
        await loadPlans()
      } else {
        setActivePlan({ id: 'local', strategy, numDays, start_date: startDate, days, created_at: new Date().toISOString() })
      }
    } catch {
      setActivePlan({ id: 'local', strategy, numDays, start_date: startDate, days, created_at: new Date().toISOString() })
    }
    setSaving(false)
    setView('detail')
  }

  const handleViewPlan = (plan: MealPlan) => {
    setActivePlan(plan)
    setView('detail')
  }

  const handleDeletePlan = async (planId: string) => {
    try {
      await deleteMealPlan(userId, planId)
      await loadPlans()
    } catch { /* ignore */ }
  }

  const handleRegenerateDay = async (dayIndex: number) => {
    if (!activePlan) return
    setRegeneratingDay(dayIndex)
    setErrorMessage(null)
    try {
      const res = await regenerateDay(userId, activePlan.id, dayIndex)
      if (res.success) {
        const updatedDays = [...activePlan.days]
        updatedDays[dayIndex] = res.day
        setActivePlan({ ...activePlan, days: updatedDays })
      } else {
        setErrorMessage(res.error || 'Failed to regenerate day')
      }
    } catch {
      setErrorMessage('Network error while regenerating day')
    }
    setRegeneratingDay(null)
  }

  const handleReplaceMeal = async (dayIndex: number, mealIndex: number) => {
    if (!activePlan) return
    setReplacingMeal({ dayIndex, mealIndex })
    setErrorMessage(null)
    try {
      const res = await replaceMeal(userId, activePlan.id, dayIndex, mealIndex)
      if (res.success) {
        const updatedDays = [...activePlan.days]
        const updatedMeals = [...updatedDays[dayIndex].meals]
        updatedMeals[mealIndex] = res.meal
        updatedDays[dayIndex] = { ...updatedDays[dayIndex], meals: updatedMeals }
        setActivePlan({ ...activePlan, days: updatedDays })
      } else {
        setErrorMessage(res.error || 'Failed to replace meal')
      }
    } catch {
      setErrorMessage('Network error while replacing meal')
    }
    setReplacingMeal(null)
  }

  const handleViewRecipe = async (meal: MealData) => {
    setRecipeMeal({ name: meal.name, type: meal.type })
    setRecipeDetail(null)
    setRecipeLoading(true)

    const cacheKey = `${meal.name}|${meal.type}`
    const cached = recipeCacheRef.current[cacheKey]
    if (cached) {
      setRecipeDetail(cached)
      setRecipeLoading(false)
      return
    }

    try {
      const res = await generateRecipeDetail(meal.name, meal.type, activePlan?.strategy || strategy)
      if (res.success && res.recipe) {
        recipeCacheRef.current[cacheKey] = res.recipe
        setRecipeDetail(res.recipe)
        setRecipeLoading(false)
        return
      }
      setRecipeLoading(false)
      setErrorMessage(res.error || 'Could not load recipe details')
      return
    } catch {
      setErrorMessage('Network error while fetching recipe')
    }
    setRecipeLoading(false)
  }

  const handleCloseRecipe = () => {
    setRecipeMeal(null)
    setRecipeDetail(null)
    setErrorMessage(null)
  }

  const [applyingShopping, setApplyingShopping] = useState(false)

  const handleApplyShoppingList = async () => {
    if (!activePlan) return
    setApplyingShopping(true)
    setErrorMessage(null)
    try {
      const invStr = localStorage.getItem('meal_planner_inventory')
      const inventory: { name: string; quantity: number; unit: string }[] = invStr ? JSON.parse(invStr) : []
      const res = await applyShoppingListFromPlan(userId, activePlan.id, inventory)
      if (res.success) {
        window.location.href = '/shopping-lists'
      } else {
        setErrorMessage(res.error || 'Failed to generate shopping list')
      }
    } catch {
      setErrorMessage('Network error while generating shopping list')
    }
    setApplyingShopping(false)
  }

  const handleGenerateAll = async () => {
    if (!activePlan) return
    setGeneratedDays(null)
    setView('generating')
    setSaving(true)
    setErrorMessage(null)

    try {
      const profile = await getUserProfile(userId)
      const res = await generateMealPlan(userId, {
        strategy: activePlan.strategy, numDays: activePlan.numDays,
        startDate: activePlan.start_date || startDate,
        userProfile: profile || undefined,
      })

      if (!res.success || !res.days?.length) {
        throw new Error(res.error || 'AI returned empty result')
      }

      const days = res.days.slice(0, activePlan.numDays)
      setGeneratedDays(days)
      const saved = await createMealPlan(userId, { strategy: activePlan.strategy, numDays: activePlan.numDays, start_date: activePlan.start_date, days })
      if (saved.success) {
        setActivePlan(saved.plan)
        await loadPlans()
      } else {
        setActivePlan({ id: 'local', strategy: activePlan.strategy, numDays: activePlan.numDays, start_date: activePlan.start_date, days, created_at: new Date().toISOString() })
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setErrorMessage(msg)
    }

    setSaving(false)
    setView('detail')
  }

  const handleBack = useCallback(() => {
    setView('list')
    setActivePlan(null)
    setGeneratedDays(null)
  }, [])

  if (view === 'detail' && activePlan) {
    return (
      <MealPlanDetailView
        plan={activePlan}
        onBack={handleBack}
        onRegenerateDay={handleRegenerateDay}
        onReplaceMeal={handleReplaceMeal}
        onViewRecipe={handleViewRecipe}
        onGenerateAll={handleGenerateAll}
        onApplyShopping={handleApplyShoppingList}
        applyingShopping={applyingShopping}
        onCloseRecipe={handleCloseRecipe}
        regeneratingDay={regeneratingDay}
        replacingMeal={replacingMeal}
        recipeMeal={recipeMeal}
        recipeDetail={recipeDetail}
        recipeLoading={recipeLoading}
        errorMessage={errorMessage}
        onClearError={() => setErrorMessage(null)}
      />
    )
  }

  if (view === 'generating') {
    return (
      <GeneratingView
        strategy={strategy}
        numDays={numDays}
        saving={saving}
        error={errorMessage}
        onBack={handleBack}
      />
    )
  }

  return (
    <div className="p-6 lg:p-8 space-y-10 max-w-[1400px] mx-auto animate-fade-in">
      <div>
        <h1 className="text-[32px] font-bold text-text tracking-tight">Meal Plans</h1>
        <p className="text-text-secondary mt-1.5 text-sm">Generate, manage and review personalized AI meal plans.</p>
      </div>

      <div className="relative rounded-3xl bg-surface border border-border overflow-hidden shadow-sm">
        <div className="p-8 space-y-7">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h2 className="text-[22px] font-semibold text-text">Generate New Meal Plan</h2>
              <p className="text-sm text-text-muted mt-1">Create a personalized meal plan tailored to your goals and lifestyle.</p>
            </div>
          </div>

          <div className="h-px bg-border" />

          <section className="space-y-4">
            <div>
              <div className="flex items-center gap-2.5">
                <Wallet className="w-5 h-5 text-primary" />
                <h3 className="text-base font-semibold text-text-secondary">Strategy</h3>
              </div>
              <p className="text-xs text-text-muted mt-0.5">Choose the strategy that best matches your goal.</p>
            </div>
            <div className="flex flex-wrap gap-3">
              {strategies.map((s) => {
                const Icon = strategyIcons[s]
                const selected = strategy === s
                return (
                  <button
                    key={s}
                    onClick={() => setStrategy(s)}
                    aria-selected={selected}
                    className={cn(
                      'inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background',
                      selected
                        ? `${strategySelectedChips[s]} scale-[1.02] border text-white`
                        : 'bg-transparent border border-border text-text-secondary hover:bg-surface-variant hover:border-zinc-500'
                    )}
                  >
                    {Icon && <Icon className={cn('w-4 h-4', selected ? strategyIconColors[s] : '')} />}
                    <span>{s}</span>
                  </button>
                )
              })}
            </div>
          </section>

          <div className="h-px bg-border" />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <section className="space-y-4">
              <div className="flex items-center gap-2.5">
                <Clock3 className="w-5 h-5 text-primary" />
                <h3 className="text-base font-semibold text-text-secondary">Duration</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {[1, 3, 5, 7].map((d) => (
                  <button
                    key={d}
                    onClick={() => setNumDays(d)}
                    aria-selected={numDays === d}
                    className={cn(
                      'inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background',
                      numDays === d
                        ? 'bg-gradient-to-r from-primary to-emerald-400 text-white shadow-lg scale-[1.02] border-0'
                        : 'bg-transparent border border-border text-text-secondary hover:bg-surface-variant hover:border-zinc-500'
                    )}
                  >
                    <Clock3 className="w-4 h-4" />
                    <span>{d} {d === 1 ? 'day' : 'days'}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="space-y-4">
              <div className="flex items-center gap-2.5">
                <CalendarDays className="w-5 h-5 text-primary" />
                <h3 className="text-base font-semibold text-text-secondary">Start Date</h3>
              </div>
              <div className="relative">
                <CalendarDays className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted pointer-events-none" />
                <input
                  type="date"
                  value={startDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full pl-12 pr-4 py-2.5 rounded-xl bg-background border border-border text-text text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200"
                />
              </div>
            </section>
          </div>

          <div className="h-px bg-border" />

          <div className="flex flex-col sm:flex-row items-stretch gap-4">
            <button
              onClick={handleGenerate}
              disabled={saving}
              className="inline-flex items-center justify-center gap-2.5 px-7 py-3 rounded-xl bg-gradient-to-r from-primary to-emerald-400 text-white font-medium text-sm shadow-md hover:shadow-lg hover:-translate-y-1 hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-md transition-all duration-200 h-12 flex-1"
            >
              {saving ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Sparkles className="w-5 h-5" />
              )}
              {saving ? 'Generating...' : 'Generate Meal Plan'}
            </button>
            <button
              onClick={handleGenerateOffline}
              disabled={saving}
              className="inline-flex items-center justify-center gap-2.5 px-7 py-3 rounded-xl bg-transparent border border-border text-text-secondary font-medium text-sm hover:bg-surface-variant hover:border-zinc-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 h-12 flex-1"
            >
              <ClipboardList className="w-5 h-5" />
              Generate Offline (No AI)
            </button>
          </div>
        </div>
      </div>

      {plans.length === 0 ? (
        <div className="flex flex-col items-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
            <UtensilsCrossed className="w-8 h-8 text-primary" />
          </div>
          <h3 className="text-xl font-semibold text-text mb-2">No Meal Plans Yet</h3>
          <p className="text-sm text-text-muted max-w-md mb-6">Generate your first personalized meal plan to get started.</p>
          <button
            onClick={handleGenerate}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-primary to-emerald-400 text-white font-medium text-sm shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200"
          >
            <Sparkles className="w-4 h-4" />
            Generate Meal Plan
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <h2 className="text-[22px] font-semibold text-text">Saved Meal Plans</h2>
            <p className="text-sm text-text-muted mt-1">View and manage previously generated meal plans.</p>
          </div>
          <div className="space-y-3">
            {plans.map((plan) => {
              const cost = plan.days.reduce((sum, d) =>
                sum + d.meals.reduce((s, m) => s + (m.cost || 0), 0), 0
              )
              const PlanIcon = strategyIcons[plan.strategy] || UtensilsCrossed
              return (
                <div
                  key={plan.id}
                  className="flex items-center gap-5 p-6 rounded-[20px] bg-surface border border-border hover:-translate-y-1 hover:shadow-xl transition-all duration-200"
                >
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${strategyContainers[plan.strategy] || 'bg-primary/10 text-primary'}`}>
                    <PlanIcon className="w-6 h-6" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-text">{plan.strategy} Meal Plan</h3>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${strategyColors[plan.strategy] || 'bg-primary/10 text-primary border-primary/20'}`}>
                        {plan.strategy}
                      </span>
                      <span className="text-xs text-text-muted">{plan.numDays} {plan.numDays === 1 ? 'Day' : 'Days'}</span>
                      <span className="text-xs text-text-muted">📅 {plan.start_date ? formatDateRange(plan.start_date, plan.numDays) : new Date(plan.created_at).toLocaleDateString()}</span>
                      <span className="text-xs text-text-muted">🍽 3 Meals / Day</span>
                      <span className="text-xs text-text-muted">💰 Est. ${cost.toFixed(2)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleViewPlan(plan)}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-all duration-200"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); window.location.href = '/shopping-lists' }}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-surface-variant text-text-muted text-xs font-medium hover:bg-surface-hover hover:text-text-secondary transition-all duration-200"
                    >
                      <ShoppingCart className="w-3.5 h-3.5" />
                      List
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeletePlan(plan.id) }}
                      className="p-2 rounded-xl hover:bg-surface-variant text-text-muted hover:text-error transition-all duration-200"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

interface GeneratingViewProps {
  strategy: string
  numDays: number
  saving: boolean
  error: string | null
  onBack: () => void
}

function GeneratingView({ strategy, numDays, saving, error, onBack }: GeneratingViewProps) {
  return (
    <div className="min-h-[80vh] flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        <div className="relative rounded-2xl bg-surface border border-border p-10 text-center space-y-6 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-primary/[0.02] to-transparent pointer-events-none" />

          {error ? (
            <>
              <div className="w-16 h-16 rounded-2xl bg-error/10 flex items-center justify-center mx-auto">
                <AlertCircle className="w-8 h-8 text-error" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-text">Failed to Generate</h2>
                <p className="text-sm text-text-muted">{error}</p>
              </div>
              <button
                onClick={onBack}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl border border-border text-text-secondary text-sm font-medium hover:bg-surface-variant hover:border-zinc-500 transition-all duration-200"
              >
                <ArrowLeft className="w-4 h-4" />
                Go Back
              </button>
            </>
          ) : saving ? (
            <>
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto animate-pulse-glow">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-text">Generating Meal Plan</h2>
                <p className="text-sm text-text-muted">
                  AI is preparing your {strategy.toLowerCase()} plan for {numDays} {numDays === 1 ? 'day' : 'days'}
                </p>
              </div>
              <div className="flex items-center justify-center gap-2 text-xs text-text-muted">
                <span className="w-1.5 h-1.5 rounded-full bg-primary/50 animate-pulse" />
                This usually takes 10–20 seconds
                <span className="w-1.5 h-1.5 rounded-full bg-primary/50 animate-pulse" />
              </div>
            </>
          ) : (
            <>
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-text">Meal Plan Ready</h2>
                <p className="text-sm text-text-muted">Your {strategy.toLowerCase()} plan is complete.</p>
              </div>
              <button
                onClick={onBack}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl border border-border text-text-secondary text-sm font-medium hover:bg-surface-variant hover:border-zinc-500 transition-all duration-200"
              >
                View Plans
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

interface MealPlanDetailViewProps {
  plan: MealPlan
  onBack: () => void
  onRegenerateDay: (dayIndex: number) => Promise<void>
  onReplaceMeal: (dayIndex: number, mealIndex: number) => Promise<void>
  onViewRecipe: (meal: MealData) => void
  onGenerateAll: () => void
  onApplyShopping: () => Promise<void>
  applyingShopping: boolean
  onCloseRecipe: () => void
  regeneratingDay: number | null
  replacingMeal: { dayIndex: number; mealIndex: number } | null
  recipeMeal: { name: string; type: string } | null
  recipeDetail: RecipeDetail | null
  recipeLoading: boolean
  errorMessage: string | null
  onClearError: () => void
}

const filterChips = [
  { label: 'All', emoji: null },
  { label: 'Breakfast', emoji: '\u{1F305}' },
  { label: 'Lunch', emoji: '\u2600\uFE0F' },
  { label: 'Dinner', emoji: '\u{1F319}' },
  { label: 'Snack', emoji: '\u{1F34E}' },
]

function MealPlanDetailView({ plan, onBack, onRegenerateDay, onReplaceMeal, onViewRecipe, onGenerateAll, onApplyShopping, applyingShopping, onCloseRecipe, regeneratingDay, replacingMeal, recipeMeal, recipeDetail, recipeLoading, errorMessage, onClearError }: MealPlanDetailViewProps) {
  const [expandedDay, setExpandedDay] = useState(plan.days.length > 0 ? String(plan.days[0].day) : '')

  const totalCost = plan.days.reduce((sum, d) =>
    sum + d.meals.reduce((s, m) => s + (m.cost || 0), 0), 0
  )
  const avgCalories = plan.days.length > 0
    ? Math.round(plan.days.reduce((sum, d) =>
        sum + d.meals.reduce((s, m) => s + (m.calories || 0), 0), 0
      ) / plan.days.length)
    : 0
  const avgProtein = plan.days.length > 0
    ? Math.round(plan.days.reduce((sum, d) =>
        sum + d.meals.reduce((s, m) => s + (m.protein || 0), 0), 0
      ) / plan.days.length)
    : 0
  const avgCarbs = plan.days.length > 0
    ? Math.round(plan.days.reduce((sum, d) =>
        sum + d.meals.reduce((s, m) => s + (m.carbs || 0), 0), 0
      ) / plan.days.length)
    : 0
  const avgFat = plan.days.length > 0
    ? Math.round(plan.days.reduce((sum, d) =>
        sum + d.meals.reduce((s, m) => s + (m.fat || 0), 0), 0
      ) / plan.days.length)
    : 0

  const totalMeals = plan.days.reduce((sum, d) => sum + d.meals.length, 0)

  const dateLabel = plan.start_date
    ? formatDateRange(plan.start_date, plan.numDays)
    : new Date(plan.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
      <MealPlanHeader
        plan={plan}
        dateLabel={dateLabel}
        onBack={onBack}
        onGenerateAll={onGenerateAll}
        onApplyShopping={onApplyShopping}
        applyingShopping={applyingShopping}
        strategyIcon={strategyIcons[plan.strategy] || UtensilsCrossed}
        strategyContainer={strategyContainers[plan.strategy] || 'bg-primary/10 text-primary'}
        strategyBadge={strategyColors[plan.strategy] || 'bg-primary/10 text-primary border-primary/20'}
      />

      {errorMessage && (
        <div className="flex items-start gap-3 px-5 py-4 rounded-2xl bg-error/10 border border-error/20 text-error text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="flex-1">{errorMessage}</div>
          <button onClick={onClearError} className="shrink-0 text-error/50 hover:text-error transition-colors">&times;</button>
        </div>
      )}

      <MealStats
        totalCost={totalCost}
        avgCalories={avgCalories}
        avgProtein={avgProtein}
        avgCarbs={avgCarbs}
        avgFat={avgFat}
        totalMeals={totalMeals}
        numDays={plan.numDays}
      />

      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
        {filterChips.map((chip) => (
          <button
            key={chip.label}
            className={cn(
              'inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all duration-200',
              chip.label === 'All'
                ? 'bg-primary text-white shadow-md'
                : 'bg-surface border border-border text-text-secondary hover:bg-surface-variant hover:border-zinc-500'
            )}
          >
            {chip.emoji && <span>{chip.emoji}</span>}
            {chip.label}
          </button>
        ))}
      </div>

      <div className="space-y-8">
        {plan.days.map((day, dayIndex) => {
          const dayHeader = getDayDate(plan.start_date, dayIndex, day.day)
          return (
            <MealDayCard
              key={day.day}
              day={day}
              dayIndex={dayIndex}
              dayHeader={dayHeader}
              expanded={expandedDay === day.day}
              onToggle={() => setExpandedDay(expandedDay === day.day ? '' : day.day)}
              onRegenerateDay={onRegenerateDay}
              onReplaceMeal={onReplaceMeal}
              onViewRecipe={onViewRecipe}
              regeneratingDay={regeneratingDay}
              replacingMeal={replacingMeal}
            />
          )
        })}
      </div>

      {recipeMeal && (
        <RecipeDetailModal
          mealName={recipeMeal.name}
          mealType={recipeMeal.type}
          strategy={plan.strategy}
          detail={recipeDetail}
          loading={recipeLoading}
          error={errorMessage}
          onClose={onCloseRecipe}
        />
      )}
    </div>
  )
}
