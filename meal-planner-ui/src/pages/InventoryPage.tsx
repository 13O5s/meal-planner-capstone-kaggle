import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Search, Plus, Package, Trash2, ChevronDown,
  Pencil,
  Folder, Flame, Beef, Wheat, Droplets, Ellipsis,
} from 'lucide-react'
import { useWorkflowStore } from '@/stores/workflow-store'
import { getSessionState, getIngredientCatalog, updateSessionState, fatsecretSearch, fatsecretGetFood } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { IngredientCatalogEntry, FatSecretFood } from '@/lib/api'

interface NutritionInfo {
  calories_per_100g: number
  protein_per_100g: number
  carbs_per_100g: number
  fat_per_100g: number
}

interface InventoryItem {
  id: string
  name: string
  quantity: number
  unit: string
  category: string
  nutrition?: NutritionInfo | null
}

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

const categoryContainers: Record<string, string> = {
  'Fruits': 'bg-orange-500/10 text-orange-400',
  'Vegetables': 'bg-emerald-500/10 text-emerald-400',
  'Meat': 'bg-rose-500/10 text-rose-400',
  'Seafood': 'bg-cyan-500/10 text-cyan-400',
  'Dairy': 'bg-blue-500/10 text-blue-400',
  'Eggs': 'bg-yellow-500/10 text-yellow-400',
  'Grains': 'bg-amber-500/10 text-amber-400',
  'Legumes': 'bg-lime-500/10 text-lime-400',
  'Nuts & Seeds': 'bg-orange-500/10 text-orange-400',
  'Herbs & Spices': 'bg-emerald-500/10 text-emerald-400',
  'Oils & Fats': 'bg-yellow-500/10 text-yellow-400',
  'Pantry': 'bg-slate-500/10 text-slate-400',
  'Frozen': 'bg-sky-500/10 text-sky-400',
  'Beverages': 'bg-teal-500/10 text-teal-400',
  'Bakery': 'bg-stone-500/10 text-stone-400',
  'Snacks': 'bg-pink-500/10 text-pink-400',
}

const STORAGE_KEY = 'meal_planner_inventory'

function loadLocalItems(): InventoryItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function saveLocalItems(items: InventoryItem[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
}

function getItemStatus(item: InventoryItem): { label: string; color: string } {
  if (item.quantity <= 1) return { label: 'Low Stock', color: 'bg-blue/10 text-blue' }
  return { label: 'Fresh', color: 'bg-primary/10 text-primary' }
}

export function InventoryPage() {
  const lastSessionId = useWorkflowStore((s) => s.lastSessionId)
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<InventoryItem[]>(() => loadLocalItems())
  const [catalog, setCatalog] = useState<IngredientCatalogEntry[]>([])
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')

  const [showAddForm, setShowAddForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newQty, setNewQty] = useState('1')
  const [newUnit, setNewUnit] = useState('piece')
  const [newCategory, setNewCategory] = useState('')
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null)

  const [selectedNutrition, setSelectedNutrition] = useState<NutritionInfo | null>(null)
  const [fatSecretResults, setFatSecretResults] = useState<FatSecretFood[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [isLoadingNutrition, setIsLoadingNutrition] = useState(false)
  const [pendingBackfillId, setPendingBackfillId] = useState<string | null>(null)
  const [editingItemId, setEditingItemId] = useState<string | null>(null)

const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
const abortRef = useRef<AbortController | null>(null)

  const ALL_CATEGORIES = ['Fruits', 'Vegetables', 'Meat', 'Seafood', 'Dairy', 'Eggs', 'Grains', 'Legumes', 'Nuts & Seeds', 'Herbs & Spices', 'Oils & Fats', 'Pantry', 'Frozen', 'Beverages', 'Bakery', 'Snacks']
  const catalogCategories = [...new Set(catalog.map((c) => c.category))]
  const allCategories = catalogCategories.length > 0
    ? [...new Set([...ALL_CATEGORIES, ...catalogCategories])]
    : ALL_CATEGORIES

  useEffect(() => {
    if (!newName || catalog.length === 0) return
    const catEntry = catalog.find(
      (c) => c.name.toLowerCase().trim() === newName.toLowerCase().trim()
    )
    if (catEntry?.category) {
      setNewCategory(catEntry.category)
    }
  }, [newName, catalog])

  const syncToSession = useCallback(async (updatedItems: InventoryItem[]) => {
    if (!lastSessionId) return
    await updateSessionState(lastSessionId, {
      available_ingredients: updatedItems.map((i) => ({
        name: i.name,
        quantity: i.quantity,
        unit: i.unit,
        original_text: i.name,
        category: i.category,
      })),
    }).catch(() => {})
  }, [lastSessionId])

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      const cat = await getIngredientCatalog().catch(() => [])
      if (cancelled) return
      setCatalog(cat)

      if (lastSessionId) {
        const session = await getSessionState(lastSessionId).catch(() => ({} as Record<string, unknown>))
        if (cancelled) return
        const sessionItems = (session.available_ingredients as Array<Record<string, unknown>>) || []
        if (sessionItems.length > 0) {
          const local = loadLocalItems()
          const merged = [...local]
          for (const ing of sessionItems) {
            const name = (ing.name as string) || (ing.original_text as string) || ''
            if (!merged.some((i) => i.name.toLowerCase() === name.toLowerCase())) {
              const catEntry = cat.find((c) => c.name.toLowerCase() === name.toLowerCase())
              const entryNutrition = (catEntry?.nutrition && Object.keys(catEntry.nutrition).length > 0)
                ? (catEntry.nutrition as unknown as NutritionInfo)
                : undefined
              merged.push({
                id: `inv-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                name,
                quantity: (ing.quantity as number) || 0,
                unit: (ing.unit as string) || 'piece',
                category: catEntry?.category || 'unknown',
                nutrition: entryNutrition,
              })
            }
          }
          setItems(merged)
          saveLocalItems(merged)
        }
      }

      setLoading(false)
    }
    load()
    return () => { cancelled = true }
  }, [lastSessionId])

  useEffect(() => {
    saveLocalItems(items)
  }, [items])

  useEffect(() => {
    if (catalog.length === 0) return
    const CATEGORY_MAP: Record<string, string> = {
      'meat': 'Meat',
      'dairy': 'Dairy',
      'pantry': 'Pantry',
      'vegetables': 'Vegetables',
      'fruit': 'Fruits',
      'seafood': 'Seafood',
      'grains': 'Grains',
      'spices': 'Herbs & Spices',
      'condiments': 'Pantry',
      'beverages': 'Beverages',
    }
    setItems((prev) => {
      let changed = false
      const updated = prev.map((item) => {
        const lower = item.category?.toLowerCase().trim()
        if (lower && CATEGORY_MAP[lower]) {
          changed = true
          return { ...item, category: CATEGORY_MAP[lower] }
        }
        if (!item.category || item.category === 'unknown') {
          const catEntry = catalog.find(
            (c) => c.name.toLowerCase().trim() === item.name.toLowerCase().trim()
          )
          changed = true
          return { ...item, category: catEntry?.category || 'Pantry' }
        }
        return item
      })
      return changed ? updated : prev
    })
  }, [catalog])

  const handleEditItem = (item: InventoryItem) => {
    setNewName(item.name)
    setNewQty(String(item.quantity))
    setNewUnit(item.unit)
    setNewCategory(item.category)
    setSelectedNutrition(item.nutrition ?? null)
    setEditingItemId(item.id)
    setShowAddForm(true)
  }

  const saveItem = () => {
    const name = newName.trim()
    if (!name || !newCategory) return
    const qty = Number(newQty) || 1

    if (editingItemId) {
      const updated = items.map((i) =>
        i.id === editingItemId
          ? { ...i, name, quantity: qty, unit: newUnit, category: newCategory, nutrition: selectedNutrition }
          : i
      )
      setItems(updated)
      syncToSession(updated)
      resetForm()
      return
    }

    const existing = items.find(
      (i) => i.name.toLowerCase().trim() === name.toLowerCase().trim() && i.unit === newUnit
    )
    if (existing) {
      const updated = items.map((i) =>
        i.id === existing.id ? { ...i, quantity: i.quantity + qty } : i
      )
      setItems(updated)
      syncToSession(updated)
      resetForm()
      return
    }

    const nutrition = selectedNutrition ?? fatSecretResults[0]?.nutrition ?? null
    const item: InventoryItem = {
      id: `inv-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name,
      quantity: qty,
      unit: newUnit,
      category: newCategory,
      nutrition,
    }

    const updated = [...items, item]
    setItems(updated)
    syncToSession(updated)
    if (!item.nutrition) setPendingBackfillId(item.id)
    resetForm()
  }

  const resetForm = () => {
    setNewName('')
    setNewQty('1')
    setNewUnit('piece')
    setNewCategory('')
    setSelectedNutrition(null)
    setFatSecretResults([])
    setIsLoadingNutrition(false)
    setPendingBackfillId(null)
    setEditingItemId(null)
    setShowAddForm(false)
  }

  const removeItem = (id: string) => {
    const updated = items.filter((i) => i.id !== id)
    setItems(updated)
    syncToSession(updated)
  }

  const filtered = items
    .filter((item) => selectedCategory === 'All' || item.category === selectedCategory)
    .filter((item) => item.name.toLowerCase().includes(search.toLowerCase()))

  const grouped = filtered.reduce(
    (acc, item) => {
      const cat = item.category
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(item)
      return acc
    },
    {} as Record<string, InventoryItem[]>
  )

  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({})

  const toggleCard = (category: string) => {
    setExpandedCards((prev) => ({ ...prev, [category]: !prev[category] }))
  }

  const CATEGORY_KEYWORDS: Record<string, string> = {
    'chicken': 'Meat', 'beef': 'Meat', 'pork': 'Meat', 'lamb': 'Meat', 'turkey': 'Meat', 'bacon': 'Meat', 'sausage': 'Meat', 'ham': 'Meat',
    'salmon': 'Seafood', 'tuna': 'Seafood', 'shrimp': 'Seafood', 'fish': 'Seafood', 'cod': 'Seafood', 'tilapia': 'Seafood',
    'milk': 'Dairy', 'cheese': 'Dairy', 'yogurt': 'Dairy', 'cream': 'Dairy', 'butter': 'Dairy', 'sour cream': 'Dairy',
    'egg': 'Eggs',
    'rice': 'Grains', 'pasta': 'Grains', 'bread': 'Bakery', 'flour': 'Grains', 'oat': 'Grains', 'noodle': 'Grains', 'quinoa': 'Grains',
    'apple': 'Fruits', 'banana': 'Fruits', 'orange': 'Fruits', 'berry': 'Fruits', 'grape': 'Fruits', 'lemon': 'Fruits',
    'tomato': 'Vegetables', 'lettuce': 'Vegetables', 'spinach': 'Vegetables', 'broccoli': 'Vegetables', 'carrot': 'Vegetables',
    'onion': 'Vegetables', 'garlic': 'Vegetables', 'potato': 'Vegetables', 'cucumber': 'Vegetables', 'pepper': 'Vegetables',
    'almond': 'Nuts & Seeds', 'walnut': 'Nuts & Seeds', 'peanut': 'Nuts & Seeds', 'cashew': 'Nuts & Seeds',
    'olive oil': 'Oils & Fats', 'coconut oil': 'Oils & Fats', 'vegetable oil': 'Oils & Fats',
    'water': 'Beverages', 'juice': 'Beverages', 'coffee': 'Beverages', 'tea': 'Beverages', 'soda': 'Beverages',
  }

  const detectCategory = (name: string): string => {
    const lower = name.toLowerCase()
    for (const [keyword, cat] of Object.entries(CATEGORY_KEYWORDS)) {
      if (lower.includes(keyword)) return cat
    }
    const catEntry = catalog.find((c) => c.name.toLowerCase().trim() === lower.trim())
    if (catEntry?.category) return catEntry.category
    return 'Pantry'
  }

  const handleNameChange = (value: string) => {
    setNewName(value)
    setSelectedNutrition(null)
    if (value.length < 2) { setFatSecretResults([]); return }

    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current)
    abortRef.current?.abort()

    const controller = new AbortController()
    abortRef.current = controller

    setIsSearching(true)
    searchTimeoutRef.current = setTimeout(async () => {
      const results = await fatsecretSearch(value)
      if (!controller.signal.aborted) {
        setFatSecretResults(results)
        setIsSearching(false)
      }
    }, 300)
  }

  const handleSelectFood = (food: FatSecretFood) => {
    setNewName(food.name)
    setNewCategory(detectCategory(food.name))
    setSelectedNutrition(food.nutrition)
    setFatSecretResults([])
    if (!food.nutrition) {
      setIsLoadingNutrition(true)
      fatsecretGetFood(food.food_id).then((detail) => {
        if (detail?.nutrition) setSelectedNutrition(detail.nutrition)
        setIsLoadingNutrition(false)
      })
    }
  }

  useEffect(() => {
    if (!selectedNutrition || !pendingBackfillId) return
    setItems((prev) =>
      prev.map((i) =>
        i.id === pendingBackfillId && !i.nutrition
          ? { ...i, nutrition: selectedNutrition }
          : i
      )
    )
    setPendingBackfillId(null)
  }, [selectedNutrition])

  useEffect(() => {
    if (!activeMenuId) return
    const handler = () => setActiveMenuId(null)
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [activeMenuId])

  const categoryCount = items.length > 0 ? new Set(items.map((i) => i.category)).size : 0

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="h-9 w-48 rounded-lg bg-surface animate-shimmer" />
            <div className="h-5 w-72 rounded bg-surface animate-shimmer mt-2" />
          </div>
          <div className="flex gap-3">
            <div className="h-12 w-40 rounded-xl bg-surface animate-shimmer" />
            <div className="h-12 w-40 rounded-xl bg-surface animate-shimmer" />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="h-9 w-40 rounded-full bg-surface animate-shimmer" />
          <div className="h-9 w-36 rounded-full bg-surface animate-shimmer" />
        </div>
        <div className="h-12 rounded-xl bg-surface animate-shimmer" />
        <div className="flex gap-2.5">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-11 w-24 rounded-full bg-surface animate-shimmer" />
          ))}
        </div>
        <div className="space-y-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className="space-y-4">
              <div className="h-8 w-48 rounded-lg bg-surface animate-shimmer" />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[1, 2].map((c) => (
                  <div key={c} className="p-5 rounded-2xl bg-surface border border-border animate-shimmer">
                    <div className="w-10 h-10 rounded-xl bg-background mb-3" />
                    <div className="h-5 w-32 rounded bg-background mb-2" />
                    <div className="h-4 w-20 rounded bg-background mb-3" />
                    <div className="space-y-1.5">
                      <div className="h-4 w-28 rounded bg-background" />
                      <div className="h-4 w-24 rounded bg-background" />
                      <div className="h-4 w-20 rounded bg-background" />
                      <div className="h-4 w-26 rounded bg-background" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
      {/* ─── Header ─── */}
      <div className="flex items-start justify-between flex-wrap gap-6">
        <div>
          <h1 className="text-4xl font-bold text-text tracking-tight">Inventory</h1>
          <p className="text-sm text-text-secondary mt-1.5">Manage all available ingredients in your pantry.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            size="lg"
            className="h-12 rounded-xl bg-gradient-to-r from-primary to-emerald-400 hover:scale-[1.02] transition-all duration-200 shadow-md shadow-primary/20"
            onClick={() => { if (showAddForm) resetForm(); else setShowAddForm(true) }}
          >
            <Plus className="w-4 h-4" />
            Add Ingredient
          </Button>
        </div>
      </div>

      {/* ─── Inventory Summary Badges ─── */}
      {items.length > 0 && (
        <div className="flex items-center gap-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface border border-border text-sm font-medium text-text">
            <Package className="w-4 h-4 text-primary" />
            {items.length} Ingredient{items.length !== 1 ? 's' : ''}
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface border border-border text-sm font-medium text-text">
            <Folder className="w-4 h-4 text-blue" />
            {categoryCount} Categor{categoryCount !== 1 ? 'ies' : 'y'}
          </div>
        </div>
      )}

      {/* ─── Add Form ─── */}
      {showAddForm && (
        <div className="rounded-2xl bg-surface border border-border p-6 space-y-4 transition-all duration-200">
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[200px] relative">
              <label className="text-text-muted text-xs font-medium uppercase tracking-wide mb-1.5 block">Ingredient</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="e.g. chicken breast"
                className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-text text-sm placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"
                autoFocus
                onKeyDown={(e) => { if (e.key === 'Enter') saveItem() }}
              />
              {isSearching && (
                <div className="absolute z-10 top-full mt-1 left-0 right-0 bg-surface border border-border rounded-xl shadow-xl overflow-hidden">
                  <div className="px-4 py-2.5 text-sm text-text-muted">Searching...</div>
                </div>
              )}
              {!isSearching && fatSecretResults.length > 0 && (
                <div className="absolute z-10 top-full mt-1 left-0 right-0 bg-surface border border-border rounded-xl shadow-xl overflow-hidden max-h-60 overflow-y-auto">
                  {fatSecretResults.map((food) => (
                    <button
                      key={food.food_id}
                      onClick={() => handleSelectFood(food)}
                      className="w-full text-left px-4 py-2.5 text-sm text-text-secondary hover:bg-surface-hover transition-colors cursor-pointer border-b border-border/50 last:border-0"
                    >
                      <span className="font-medium text-text capitalize">{food.name}</span>
                      {food.brand && <span className="text-text-muted ml-1">— {food.brand}</span>}
                      <div className="flex gap-2 mt-0.5 text-xs text-text-muted">
                        {food.nutrition && (
                          <>
                            <span>{food.nutrition.calories_per_100g} kcal</span>
                            <span>P:{food.nutrition.protein_per_100g}g</span>
                            <span>C:{food.nutrition.carbs_per_100g}g</span>
                            <span>F:{food.nutrition.fat_per_100g}g</span>
                          </>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="w-20">
              <label className="text-text-muted text-xs font-medium uppercase tracking-wide mb-1.5 block">Qty</label>
              <input
                type="number"
                value={newQty}
                onChange={(e) => setNewQty(e.target.value)}
                min={0}
                step={0.5}
                className="w-full px-3 py-2.5 rounded-xl bg-background border border-border text-text text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all duration-200"
              />
            </div>
            <div className="w-24">
              <label className="text-text-muted text-xs font-medium uppercase tracking-wide mb-1.5 block">Unit</label>
              <select
                value={newUnit}
                onChange={(e) => setNewUnit(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-background border border-border text-text text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all duration-200"
              >
                <option value="piece">piece</option>
                <option value="g">g</option>
                <option value="kg">kg</option>
                <option value="ml">ml</option>
                <option value="L">L</option>
                <option value="tbsp">tbsp</option>
                <option value="cup">cup</option>
              </select>
            </div>
            <div className="w-32">
              <label className="text-text-muted text-xs font-medium uppercase tracking-wide mb-1.5 block">Category</label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-background border border-border text-text text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all duration-200 capitalize"
              >
                <option value="">Select...</option>
                {allCategories.map((cat) => (
                  <option key={cat} value={cat} className="capitalize">{cat}</option>
                ))}
              </select>
            </div>
            <button
              onClick={saveItem}
              className="px-5 py-2.5 rounded-xl bg-primary text-on-primary text-sm font-medium hover:bg-primary-hover transition-colors duration-200"
            >
              {editingItemId ? 'Update' : 'Add'}
            </button>
            {isLoadingNutrition && (
              <span className="text-xs text-text-muted animate-pulse">Loading nutrition...</span>
            )}
            <button
              onClick={resetForm}
              className="px-5 py-2.5 rounded-xl bg-transparent border border-border text-text-secondary text-sm font-medium hover:bg-surface-variant transition-colors duration-200"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* ─── Search & Toolbar ─── */}
      <div className="flex flex-col gap-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
          <input
            type="search"
            placeholder="Search ingredients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-[52px] pl-12 pr-4 rounded-full bg-surface border border-border text-text text-base placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"
          />
        </div>

        {/* ─── Category Filters ─── */}
        <div className="flex gap-2.5 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => setSelectedCategory('All')}
            className={cn(
              'shrink-0 inline-flex items-center gap-2 px-5 h-[44px] rounded-full text-sm font-medium transition-all duration-200',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
              selectedCategory === 'All'
                ? 'bg-primary text-on-primary shadow-sm shadow-primary/20 scale-[1.02]'
                : 'bg-transparent border border-border text-text-secondary hover:bg-surface-variant hover:border-border hover:text-text'
            )}
          >
            All
          </button>
          {ALL_CATEGORIES.filter(cat => items.some(i => i.category === cat)).map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                'shrink-0 inline-flex items-center gap-2 px-5 h-[44px] rounded-full text-sm font-medium transition-all duration-200',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
                selectedCategory === cat
                  ? 'bg-primary text-on-primary shadow-sm shadow-primary/20 scale-[1.02]'
                  : 'bg-transparent border border-border text-text-secondary hover:bg-surface-variant hover:border-border hover:text-text'
              )}
            >
              <span className="text-base">{categoryEmojis[cat] || '📦'}</span>
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* ─── Empty State ─── */}
      {items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-20 h-20 rounded-2xl bg-surface border border-border flex items-center justify-center mb-6">
            <Package className="w-10 h-10 text-text-muted" />
          </div>
          <h3 className="text-xl font-semibold text-text">Inventory is Empty</h3>
          <p className="text-text-secondary mt-2 max-w-sm">
            Add ingredients to receive better meal recommendations and shopping suggestions.
          </p>
          <div className="flex items-center gap-3 mt-6">
            <Button
              size="lg"
              className="h-12 rounded-xl bg-gradient-to-r from-primary to-emerald-400 hover:scale-[1.02] transition-all duration-200 shadow-md shadow-primary/20"
              onClick={() => { resetForm(); setShowAddForm(true) }}
            >
              <Plus className="w-4 h-4" />
              Add Ingredient
            </Button>
          </div>
        </div>
      )}
      {/* ─── No Results ─── */}

      {/* ─── No Results ─── */}
      {items.length > 0 && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-surface border border-border flex items-center justify-center mb-5">
            <Search className="w-8 h-8 text-text-muted" />
          </div>
          <h3 className="text-lg font-semibold text-text">No ingredients found</h3>
          <p className="text-text-secondary mt-1.5 text-sm max-w-sm">
            Try adjusting your search or category filter.
          </p>
          <Button
            size="lg"
            className="mt-5 h-12 rounded-xl bg-gradient-to-r from-primary to-emerald-400 hover:scale-[1.02] transition-all duration-200 shadow-md shadow-primary/20"
            onClick={() => { resetForm(); setShowAddForm(true) }}
          >
            <Plus className="w-4 h-4" />
            Add Ingredient
          </Button>
        </div>
      )}

      {/* ─── Category Sections ─── */}
      {Object.entries(grouped).map(([category, catItems], sectionIndex) => {
        const isExpanded = expandedCards[category] !== false
        const emoji = categoryEmojis[category] || '📦'
        const containerClasses = categoryContainers[category] || 'bg-primary/10 text-primary'
        return (
          <div key={category} className="space-y-4">
            {/* Section Divider (skip for first section) */}
            {sectionIndex > 0 && (
              <div className="border-t border-border/50" />
            )}

            {/* Category Header — sticky */}
            <div className="flex items-center justify-between sticky top-0 z-10 bg-background pt-2 pb-1 -mx-6 lg:-mx-8 px-6 lg:px-8">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${containerClasses}`}>
                  <span className="text-lg leading-none">{emoji}</span>
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text">{category}</h2>
                  <p className="text-xs text-text-secondary">
                    {catItems.length} Ingredient{catItems.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleCard(category)}
                  className="p-1.5 rounded-lg hover:bg-surface-variant text-text-muted hover:text-text transition-all duration-200"
                  aria-label={isExpanded ? 'Collapse category' : 'Expand category'}
                >
                  <ChevronDown className={cn(
                    'w-4 h-4 transition-transform duration-200',
                    isExpanded && 'rotate-180'
                  )} />
                </button>
              </div>
            </div>

            {/* Ingredient Grid — compact, left-aligned cards */}
            {isExpanded && (
              <div className="flex flex-wrap gap-4">
                {catItems.map((item) => {
                  const status = getItemStatus(item)
                  const n = item.nutrition
                  return (
                    <div
                      key={item.id}
                      className="group flex-grow min-w-[280px] max-w-[360px] p-4 rounded-2xl bg-surface border border-border/50 shadow-sm hover:-translate-y-1 hover:shadow-xl transition-all duration-200"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <h3 className="text-sm font-semibold text-text capitalize truncate">{item.name}</h3>
                          <p className="text-xs text-text-secondary mt-0.5">
                            {emoji} {item.quantity} {item.unit}
                          </p>
                        </div>

                        {/* Three-dot menu */}
                        <div className="relative shrink-0">
                          <button
                            onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === item.id ? null : item.id) }}
                            className="p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-surface-hover text-text-muted hover:text-text transition-all duration-200"
                            aria-label="Item actions"
                          >
                            <Ellipsis className="w-3.5 h-3.5" />
                          </button>
                          {activeMenuId === item.id && (
                            <div
                              className="absolute right-0 top-full mt-1 w-44 rounded-xl bg-surface border border-border shadow-xl overflow-hidden z-20"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <button
                                onClick={() => { handleEditItem(item); setActiveMenuId(null) }}
                                className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs text-text hover:bg-surface-hover transition-colors"
                              >
                                <Pencil className="w-3.5 h-3.5 text-text-muted" />
                                Edit
                              </button>
                              <button
                                onClick={() => { removeItem(item.id); setActiveMenuId(null) }}
                                className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs text-error hover:bg-error/10 transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                                Delete
                              </button>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Nutrition badges — always visible, compact */}
                      <div className="flex flex-wrap gap-1 mt-2.5">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-variant text-[11px] font-medium text-text">
                          <Flame className="w-3 h-3 text-blue shrink-0" />
                          {n?.calories_per_100g != null ? n.calories_per_100g : <span className="text-text-muted">--</span>}
                        </span>
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-variant text-[11px] font-medium text-text">
                          <Beef className="w-3 h-3 text-error shrink-0" />
                          {n?.protein_per_100g != null ? <>{n.protein_per_100g}g</> : <span className="text-text-muted">--</span>}
                        </span>
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-variant text-[11px] font-medium text-text">
                          <Wheat className="w-3 h-3 text-warning shrink-0" />
                          {n?.carbs_per_100g != null ? <>{n.carbs_per_100g}g</> : <span className="text-text-muted">--</span>}
                        </span>
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-variant text-[11px] font-medium text-text">
                          <Droplets className="w-3 h-3 text-primary shrink-0" />
                          {n?.fat_per_100g != null ? <>{n.fat_per_100g}g</> : <span className="text-text-muted">--</span>}
                        </span>
                      </div>

                      {/* Status badge */}
                      <div className="mt-2.5">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium ${status.color}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${status.color.split(' ')[0].replace('bg-', 'bg-')}`} />
                          {status.label}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Collapsed indicator */}
            {!isExpanded && (
              <p className="text-sm text-text-muted px-1 py-1">{catItems.length} ingredient{catItems.length !== 1 ? 's' : ''} hidden</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
