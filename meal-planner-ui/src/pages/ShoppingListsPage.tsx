import { useState, useEffect } from 'react'
import {
  ShoppingCart, Search, Check, DollarSign, Package,
  ChevronDown, CircleDollarSign
} from 'lucide-react'
import { EmptyState } from '@/components/shared/EmptyState'
import { getShoppingList, toggleShoppingItem, type ShoppingListItem } from '@/lib/api'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'

const categoryEmojis: Record<string, string> = {
  'Fruits': '🍎',
  'Vegetables': '🥦',
  'Meat': '🥩',
  'Seafood': '🐟',
  'Dairy': '🥛',
  'Eggs': '🥚',
  'Grains': '🌾',
  'Legumes': '🫘',
  'Nuts & Seeds': '🥜',
  'Herbs & Spices': '🌿',
  'Oils & Fats': '🫒',
  'Pantry': '🥫',
  'Frozen': '❄️',
  'Beverages': '🥤',
  'Bakery': '🥖',
  'Snacks': '🍪',
}

const categoryColors: Record<string, string> = {
  'Meat': 'bg-rose-500/10 text-rose-400',
  'Vegetables': 'bg-emerald-500/10 text-emerald-400',
  'Fruits': 'bg-orange-500/10 text-orange-400',
  'Dairy': 'bg-blue-500/10 text-blue-400',
  'Eggs': 'bg-yellow-500/10 text-yellow-400',
  'Seafood': 'bg-cyan-500/10 text-cyan-400',
  'Grains': 'bg-amber-500/10 text-amber-400',
  'Pantry': 'bg-slate-500/10 text-slate-400',
  'Spices': 'bg-rose-500/10 text-rose-400',
  'Herbs': 'bg-emerald-500/10 text-emerald-400',
  'Bakery': 'bg-stone-500/10 text-stone-400',
  'Drinks': 'bg-violet-500/10 text-violet-400',
}

export function ShoppingListsPage() {
  const user = useAuthStore((s) => s.user)
  const userId = user?.user_id || ''
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<(ShoppingListItem & { toggling: boolean })[]>([])
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set())
  const [totalCost, setTotalCost] = useState(0)

  const fetchList = async () => {
    if (!userId) { setLoading(false); return }
    setLoading(true)
    try {
      const res = await getShoppingList(userId)
      if (res.success && res.shopping_list) {
        setItems(res.shopping_list.items.map((i) => ({ ...i, toggling: false })))
        setTotalCost(res.total_cost || 0)
      } else {
        setItems([])
      }
    } catch {
      setItems([])
    }
    setLoading(false)
  }

  useEffect(() => { fetchList() }, [userId])

  const toggleItem = async (itemId: string) => {
    if (!userId) return
    setItems((prev) => prev.map((i) => (i.id === itemId ? { ...i, toggling: true } : i)))
    try {
      const res = await toggleShoppingItem(userId, itemId)
      if (res.success && res.item) {
        setItems((prev) => prev.map((i) =>
          i.id === itemId ? { ...i, purchased: res.item!.purchased, toggling: false } : i
        ))
      }
    } catch {
      setItems((prev) => prev.map((i) => (i.id === itemId ? { ...i, toggling: false } : i)))
    }
  }

  const toggleCategory = (cat: string) => {
    setCollapsedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  const allCategoriesSet = [...new Set(items.map((i) => i.category))]
  const categoryList = ['All', ...allCategoriesSet]

  const filteredItems = items.filter((i) => {
    const matchesSearch = i.ingredient_name.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = selectedCategory === 'All' || i.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const grouped = filteredItems.reduce(
    (acc, item) => {
      const cat = item.category
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(item)
      return acc
    },
    {} as Record<string, (ShoppingListItem & { toggling: boolean })[]>
  )

  const totalItems = items.length
  const numCategories = new Set(items.map((i) => i.category)).size
  const purchased = items.filter((i) => i.purchased).length
  const totalCostValue = items.reduce((s, i) => s + i.estimated_cost, totalCost)
  const progress = items.length > 0 ? (purchased / items.length) * 100 : 0
  const hasFilteredResults = Object.keys(grouped).length > 0

  if (loading) {
    return (
      <div className="p-6 lg:p-8 max-w-[1400px] mx-auto min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          <p className="text-sm text-text-muted">Loading shopping list...</p>
        </div>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">
        <EmptyState
          icon={<ShoppingCart className="w-8 h-8" />}
          title="Your Shopping List is Empty"
          description="Generate a shopping list from your meal plans or add items manually."
        />
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
      {/* Page Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold text-text tracking-tight">Shopping List</h1>
          <p className="text-text-secondary mt-1.5 text-sm">
            Review, organize and manage ingredients you need to purchase.
          </p>
        </div>
      </div>

      {/* Summary Pills */}
      <div className="flex flex-wrap gap-2">
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-medium border border-primary/20">
          <ShoppingCart className="w-3.5 h-3.5" />
          {totalItems} Items
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-400 text-xs font-medium border border-blue-500/20">
          <Package className="w-3.5 h-3.5" />
          {numCategories} Categories
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-500/10 text-amber-400 text-xs font-medium border border-amber-500/20">
          <CircleDollarSign className="w-3.5 h-3.5" />
          ${totalCostValue.toFixed(2)}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 rounded-full bg-surface-variant overflow-hidden -mt-4">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* ─── Search & Toolbar ─── */}
      <div className="flex flex-col gap-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
          <input
            type="search"
            placeholder="Search items..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-[52px] pl-12 pr-4 rounded-full bg-surface border border-border text-text text-base placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"
          />
        </div>

        {/* ─── Category Filters ─── */}
        {categoryList.length > 1 && (
          <div className="flex gap-2.5 overflow-x-auto pb-1 scrollbar-none">
            {categoryList.map((cat) => {
              const emoji = categoryEmojis[cat]
              const selected = selectedCategory === cat
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={cn(
                    'shrink-0 inline-flex items-center gap-2 px-5 h-[44px] rounded-full text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
                    selected
                      ? 'bg-primary text-on-primary shadow-sm shadow-primary/20 scale-[1.02]'
                      : 'bg-transparent border border-border text-text-secondary hover:bg-surface-variant hover:border-border hover:text-text'
                  )}
                >
                  {cat === 'All' ? (
                    <ShoppingCart className="w-4 h-4" />
                  ) : (
                    <span className="text-base">{emoji || '📦'}</span>
                  )}
                  {cat}
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* ─── Category Sections ─── */}
      {!hasFilteredResults ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-surface border border-border flex items-center justify-center mb-5">
            <Search className="w-8 h-8 text-text-muted" />
          </div>
          <h3 className="text-lg font-semibold text-text">No items found</h3>
          <p className="text-text-secondary mt-1.5 text-sm max-w-sm">
            Try adjusting your search or category filter.
          </p>
        </div>
      ) : (
        <div>
          {Object.entries(grouped).map(([category, catItems], sectionIndex) => {
            const emoji = categoryEmojis[category]
            const colorClasses = categoryColors[category] || 'bg-primary/10 text-primary'
            const isCollapsed = collapsedCategories.has(category)

            return (
              <div key={category} className="space-y-4">
                {/* Section Divider */}
                {sectionIndex > 0 && (
                  <div className="border-t border-border/50" />
                )}

                {/* Category Header — sticky */}
                <div className="flex items-center justify-between sticky top-0 z-10 bg-background pt-2 pb-1 -mx-6 lg:-mx-8 px-6 lg:px-8">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${colorClasses}`}>
                      <span className="text-lg leading-none">{emoji || '📦'}</span>
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-text">{category}</h2>
                      <p className="text-xs text-text-secondary">
                        {catItems.length} {catItems.length === 1 ? 'item' : 'items'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-text-muted font-medium">
                      ${catItems.reduce((s, i) => s + i.estimated_cost, 0).toFixed(2)}
                    </span>
                    <button
                      onClick={() => toggleCategory(category)}
                      className="p-1.5 rounded-lg hover:bg-surface-variant text-text-muted hover:text-text transition-all duration-200"
                      aria-label={isCollapsed ? 'Expand category' : 'Collapse category'}
                    >
                      <ChevronDown className={cn(
                        'w-4 h-4 transition-transform duration-200',
                        !isCollapsed && 'rotate-180'
                      )} />
                    </button>
                  </div>
                </div>

                {/* Items List — vertical */}
                {!isCollapsed && (
                  <div className="space-y-2">
                    {catItems.map((item) => (
                      <div
                        key={item.id}
                        className={cn(
                          'flex items-center gap-4 px-5 py-4 rounded-2xl bg-surface border border-border/50 transition-all duration-200 hover:bg-surface-hover',
                          item.purchased && 'opacity-60'
                        )}
                      >
                        {/* Checkbox */}
                        <button
                          onClick={() => toggleItem(item.id)}
                          disabled={item.toggling}
                          className={cn(
                            'w-5 h-5 rounded-lg border-2 flex items-center justify-center shrink-0 transition-all duration-200 cursor-pointer',
                            item.purchased
                              ? 'bg-primary border-primary shadow-sm shadow-primary/20'
                              : 'border-border hover:border-primary hover:bg-primary/5'
                          )}
                        >
                          {item.toggling ? (
                            <div className="w-2.5 h-2.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                          ) : item.purchased ? (
                            <Check className="w-3 h-3 text-on-primary" />
                          ) : null}
                        </button>

                        {/* Name */}
                        <p className={cn(
                          'flex-1 text-sm font-medium text-text min-w-0 truncate',
                          item.purchased && 'line-through text-text-muted'
                        )}>
                          {item.ingredient_name}
                        </p>

                        {/* Quantity */}
                        <span className="text-xs text-text-secondary flex items-center gap-1 shrink-0">
                          <Package className="w-3 h-3" />
                          {item.need} {item.unit}
                        </span>

                        {/* Price */}
                        <span className="text-xs text-text-secondary flex items-center gap-1 shrink-0 min-w-[56px] justify-end">
                          <DollarSign className="w-3 h-3" />
                          ${item.estimated_cost.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Collapsed indicator */}
                {isCollapsed && (
                  <p className="text-sm text-text-muted px-1">{catItems.length} {catItems.length === 1 ? 'item' : 'items'} hidden</p>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
