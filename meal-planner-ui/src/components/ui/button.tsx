import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

const variants = {
  primary:
    'bg-primary text-on-primary hover:bg-primary-hover shadow-sm shadow-primary/20',
  secondary:
    'bg-surface-variant text-text hover:bg-surface-hover',
  ghost:
    'bg-transparent hover:bg-surface-variant text-text-secondary',
  outline:
    'border border-border bg-transparent text-text hover:bg-surface-variant',
  danger:
    'bg-error/10 text-error hover:bg-error/20',
}

const sizes = {
  sm: 'px-3 py-1.5 text-xs rounded-xl',
  md: 'px-5 py-2.5 text-sm rounded-xl',
  lg: 'px-7 py-3 text-base rounded-xl',
  icon: 'p-2 rounded-xl',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants
  size?: keyof typeof sizes
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:pointer-events-none cursor-pointer',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  )
)
Button.displayName = 'Button'
