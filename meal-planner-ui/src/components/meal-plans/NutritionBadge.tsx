import { cn } from '@/lib/utils'

const colorStyles = {
  calories: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  protein: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  carbs: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  fat: 'bg-green-500/10 text-green-400 border-green-500/20',
  time: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  cost: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
}

interface NutritionBadgeProps {
  icon: string
  value: string
  color: keyof typeof colorStyles
}

export function NutritionBadge({ icon, value, color }: NutritionBadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border',
      colorStyles[color]
    )}>
      <span className="text-[10px]">{icon}</span>
      <span>{value}</span>
    </span>
  )
}
