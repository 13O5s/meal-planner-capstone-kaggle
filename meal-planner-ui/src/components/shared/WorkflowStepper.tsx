import { Check, Loader2, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { WorkflowStep } from '@/types'

interface WorkflowStepperProps {
  steps: WorkflowStep[]
  className?: string
}

const statusIcon = (status: WorkflowStep['status']) => {
  switch (status) {
    case 'completed':
      return <Check className="w-4 h-4" />
    case 'active':
      return <Loader2 className="w-4 h-4 animate-spin" />
    case 'error':
      return <X className="w-4 h-4" />
    default:
      return <div className="w-2 h-2 rounded-full bg-outline-variant dark:bg-outline-variant-dark" />
  }
}

const statusColor = (status: WorkflowStep['status']) => {
  switch (status) {
    case 'completed':
      return 'bg-primary dark:bg-primary-dark text-on-primary'
    case 'active':
      return 'bg-tertiary dark:bg-tertiary-dark text-on-tertiary animate-pulse'
    case 'error':
      return 'bg-error dark:bg-error-dark text-on-error'
    default:
      return 'bg-surface-variant dark:bg-surface-variant-dark'
  }
}

export function WorkflowStepper({ steps, className }: WorkflowStepperProps) {
  return (
    <div className={cn('space-y-0', className)}>
      {steps.map((step, index) => (
        <div key={step.id} className="relative flex gap-4 pb-6 last:pb-0">
          {index < steps.length - 1 && (
            <div
              className={cn(
                'absolute left-[15px] top-8 w-0.5 h-full -translate-x-1/2',
                step.status === 'completed'
                  ? 'bg-primary dark:bg-primary-dark'
                  : 'bg-outline-variant dark:bg-outline-variant-dark'
              )}
            />
          )}

          <div
            className={cn(
              'relative z-10 w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-all duration-300',
              statusColor(step.status)
            )}
          >
            {statusIcon(step.status)}
          </div>

          <div className="flex-1 pt-1 min-w-0">
            <p
              className={cn(
                'text-sm font-medium',
                step.status === 'pending' && 'text-outline dark:text-outline-dark'
              )}
            >
              {step.label}
            </p>
            {step.duration && (
              <p className="text-xs text-outline dark:text-outline-dark mt-0.5">
                {step.duration}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
