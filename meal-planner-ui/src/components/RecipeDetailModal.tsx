import { X, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { RecipeDetail } from '@/lib/api'

interface RecipeDetailModalProps {
  mealName: string
  mealType: string
  strategy: string
  detail: RecipeDetail | null
  loading: boolean
  error: string | null
  onClose: () => void
}

export function RecipeDetailModal({ mealName, mealType, strategy, detail, loading, error, onClose }: RecipeDetailModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-12 pb-8 bg-black/50 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-surface dark:bg-surface-dark rounded-2xl shadow-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-outline-variant dark:border-outline-variant-dark">
          <div className="min-w-0 flex-1">
            <h2 className="text-h3 font-heading font-bold truncate">{mealName}</h2>
            <p className="text-sm text-outline dark:text-outline-dark">
              {mealType} &middot; {strategy} plan
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="p-5 max-h-[70vh] overflow-y-auto space-y-5">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="w-8 h-8 text-primary dark:text-primary-dark animate-spin" />
              <p className="text-sm text-outline dark:text-outline-dark">Generating recipe details...</p>
            </div>
          )}

          {!loading && !detail && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <AlertCircle className="w-8 h-8 text-error dark:text-error-dark" />
              <p className="text-sm font-medium text-center text-error dark:text-error-dark">
                {error || 'Could not generate recipe details.'}
              </p>
              <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
            </div>
          )}

          {!loading && detail && !detail.ingredients?.length && !detail.instructions?.length && (
            <div className="text-center py-4 px-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-900/30">
              <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                Gemini API quota exceeded
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
                Full ingredients and instructions are unavailable right now. Try again later or upgrade your API plan.
              </p>
            </div>
          )}

          {!loading && detail && (
            <>
              {/* Nutrition */}
              <Card>
                <CardContent className="p-4">
                  <h3 className="text-h4 font-heading font-semibold mb-3">Nutrition Facts</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                      { label: 'Calories', value: `${detail.nutrition.calories || '--'}`, color: 'bg-nutrition-calories' },
                      { label: 'Protein', value: `${detail.nutrition.protein || '--'}g`, color: 'bg-nutrition-protein' },
                      { label: 'Carbs', value: `${detail.nutrition.carbs || '--'}g`, color: 'bg-nutrition-carbs' },
                      { label: 'Fat', value: `${detail.nutrition.fat || '--'}g`, color: 'bg-nutrition-fat' },
                    ].map((n) => (
                      <div key={n.label} className="text-center p-3 rounded-xl bg-surface-variant dark:bg-surface-variant-dark">
                        <p className="text-xs text-outline dark:text-outline-dark">{n.label}</p>
                        <p className="text-h3 font-heading font-bold mt-1">{n.value}</p>
                        <div className="h-1.5 rounded-full bg-surface-dim dark:bg-surface-dim-dark mt-2 overflow-hidden">
                          <div className={`h-full rounded-full ${n.color}`} style={{ width: '60%' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Ingredients */}
              {detail.ingredients && detail.ingredients.length > 0 && (
                <Card>
                  <CardContent className="p-4">
                    <h3 className="text-h4 font-heading font-semibold mb-3">Ingredients</h3>
                    <div className="space-y-2">
                      {detail.ingredients.map((ing, i) => (
                        <div key={i} className="flex items-center gap-3 text-sm">
                          <span className="w-1.5 h-1.5 rounded-full bg-primary dark:bg-primary-dark shrink-0" />
                          <span>{ing.quantity} {ing.unit} {ing.name}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Instructions */}
              {detail.instructions && detail.instructions.length > 0 && (
                <Card>
                  <CardContent className="p-4">
                    <h3 className="text-h4 font-heading font-semibold mb-3">Instructions</h3>
                    <ol className="space-y-3">
                      {detail.instructions.map((step, i) => (
                        <li key={i} className="flex gap-3 text-sm">
                          <span className="w-6 h-6 rounded-full bg-primary-container dark:bg-primary-container-dark text-on-primary-container dark:text-on-primary-container-dark flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          <span className="leading-relaxed">{step}</span>
                        </li>
                      ))}
                    </ol>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
