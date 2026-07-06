import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-lg bg-surface-variant dark:bg-surface-variant-dark',
        className
      )}
    />
  )
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-outline-variant dark:border-outline-variant-dark p-5 space-y-4">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  )
}
