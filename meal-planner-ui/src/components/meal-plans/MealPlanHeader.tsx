import { ArrowLeft, ShoppingCart, RefreshCw, Loader2, CalendarDays, UtensilsCrossed } from 'lucide-react'
import type { MealPlan } from '@/lib/api'
import type { ComponentType } from 'react'

interface MealPlanHeaderProps {
  plan: MealPlan
  dateLabel: string
  onBack: () => void
  onGenerateAll: () => void
  onApplyShopping: () => void
  applyingShopping: boolean
  strategyIcon?: ComponentType<{ className?: string }>
  strategyContainer?: string
  strategyBadge?: string
}

export function MealPlanHeader({ plan, dateLabel, onBack, onGenerateAll, onApplyShopping, applyingShopping, strategyIcon: StrategyIcon, strategyContainer, strategyBadge }: MealPlanHeaderProps) {
  return (
    <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-9 h-9 rounded-xl bg-surface-variant hover:bg-surface-hover flex items-center justify-center transition-colors shrink-0"
          >
            <ArrowLeft className="w-4 h-4 text-text-secondary" />
          </button>
          {StrategyIcon && (
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${strategyContainer || 'bg-primary/10 text-primary'}`}>
              <StrategyIcon className="w-5 h-5" />
            </div>
          )}
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-text tracking-tight">{plan.strategy} Meal Plan</h1>
            <p className="text-sm text-text-muted mt-0.5">Generated for {dateLabel}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-4 ml-12">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${strategyBadge || 'bg-primary/10 text-primary border-primary/20'}`}>
            {StrategyIcon && <StrategyIcon className="w-3.5 h-3.5" />}
            {plan.strategy}
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-medium border border-blue-500/20">
            <CalendarDays className="w-3.5 h-3.5" />
            {plan.numDays} {plan.numDays === 1 ? 'day' : 'days'}
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-500/10 text-orange-400 text-xs font-medium border border-orange-500/20">
            <UtensilsCrossed className="w-3.5 h-3.5" />
            3 meals/day
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={onApplyShopping}
          disabled={applyingShopping}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-border text-text-secondary text-sm font-medium bg-surface hover:bg-surface-variant hover:border-primary/30 hover:text-primary transition-all duration-200 disabled:opacity-50"
        >
          {applyingShopping ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <ShoppingCart className="w-4 h-4" />
          )}
          {applyingShopping ? 'Applying...' : 'Apply to Shopping List'}
        </button>
        <button
          onClick={onGenerateAll}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-primary to-emerald-400 text-white text-sm font-semibold shadow-lg shadow-primary/20 hover:shadow-primary/30 hover:brightness-110 hover:scale-[1.02] transition-all duration-200"
        >
          <RefreshCw className="w-4 h-4" />
          Generate All
        </button>
      </div>
    </div>
  )
}
