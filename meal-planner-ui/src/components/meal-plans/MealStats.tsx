import { motion } from 'framer-motion'
import { UtensilsCrossed, Flame, Wallet, CalendarDays } from 'lucide-react'

interface MealStatsProps {
  totalCost: number
  avgCalories: number
  avgProtein: number
  avgCarbs: number
  avgFat: number
  totalMeals?: number
  numDays?: number
}

const statCards = [
  {
    icon: UtensilsCrossed,
    label: 'Total Meals',
    key: 'meals' as const,
    gradient: 'from-emerald-500/20 to-emerald-500/5',
    border: 'border-emerald-500/20',
    iconBg: 'bg-emerald-500/10',
    iconColor: 'text-emerald-400',
  },
  {
    icon: Flame,
    label: 'Avg. Calories',
    key: 'calories' as const,
    gradient: 'from-orange-500/20 to-orange-500/5',
    border: 'border-orange-500/20',
    iconBg: 'bg-orange-500/10',
    iconColor: 'text-orange-400',
  },
  {
    icon: Wallet,
    label: 'Est. Cost',
    key: 'cost' as const,
    gradient: 'from-blue-500/20 to-blue-500/5',
    border: 'border-blue-500/20',
    iconBg: 'bg-blue-500/10',
    iconColor: 'text-blue-400',
  },
  {
    icon: CalendarDays,
    label: 'Duration',
    key: 'duration' as const,
    gradient: 'from-purple-500/20 to-purple-500/5',
    border: 'border-purple-500/20',
    iconBg: 'bg-purple-500/10',
    iconColor: 'text-purple-400',
  },
]

export function MealStats({ totalCost, avgCalories, totalMeals = 21, numDays = 7 }: MealStatsProps) {
  const values = {
    meals: { display: `${totalMeals}`, sub: `Across ${numDays} ${numDays === 1 ? 'day' : 'days'}` },
    calories: { display: avgCalories.toLocaleString(), sub: 'Daily average' },
    cost: { display: `$${totalCost.toFixed(2)}`, sub: 'Total estimated' },
    duration: { display: `${numDays} ${numDays === 1 ? 'day' : 'days'}`, sub: 'Full plan' },
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {statCards.map((card, i) => {
        const v = values[card.key]
        return (
          <motion.div
            key={card.key}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.08 }}
            className={`relative rounded-2xl bg-gradient-to-br ${card.gradient} bg-surface border ${card.border} p-5 space-y-4 overflow-hidden group hover:-translate-y-1 hover:shadow-xl transition-all duration-200`}
          >
            <div className={`w-10 h-10 rounded-xl ${card.iconBg} flex items-center justify-center`}>
              <card.icon className={`w-5 h-5 ${card.iconColor}`} />
            </div>
            <div>
              <p className={`text-2xl font-bold text-text ${card.iconColor}`}>{v.display}</p>
              <p className="text-xs text-text-muted mt-1">{card.label} &middot; {v.sub}</p>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
