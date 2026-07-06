import { useState, useEffect, useRef, useCallback } from 'react'
import { Plus, X, ChevronDown, Scale, Ruler, Cake, Wallet, Activity, Flame, Target, UtensilsCrossed, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth-store'
import { getUserProfile, saveProfile } from '@/lib/api'
import { cn } from '@/lib/utils'

const GOALS = ['Weight Loss', 'Weight Gain', 'Maintain Muscle', 'General Health', 'High Protein']
const ACTIVITY_LEVELS = ['Sedentary', 'Light', 'Moderate', 'Active', 'Very Active']
const DIETARY_PREFS = ['Vegetarian', 'Vegan', 'Keto', 'Paleo', 'Mediterranean', 'Low Carb']

const ACTIVITY_REVERSE: Record<string, string> = {
  'sedentary': 'Sedentary',
  'light': 'Light',
  'moderate': 'Moderate',
  'active': 'Active',
  'very_active': 'Very Active',
}

const GOAL_REVERSE: Record<string, string> = {
  'weight_loss': 'Weight Loss',
  'maintain': 'Maintain Muscle',
  'healthy': 'General Health',
  'high_protein': 'High Protein',
}

function mapDisplay(value: string, reverseMap: Record<string, string>): string {
  return reverseMap[value] || value
}

export function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [profile, setProfile] = useState<Record<string, unknown>>({})
  const [dirty, setDirty] = useState(false)

  const [showAllergyInput, setShowAllergyInput] = useState(false)
  const [showFavoriteInput, setShowFavoriteInput] = useState(false)
  const [showDislikedInput, setShowDislikedInput] = useState(false)
  const [newAllergy, setNewAllergy] = useState('')
  const [newFavorite, setNewFavorite] = useState('')
  const [newDisliked, setNewDisliked] = useState('')
  const [prefsOpen, setPrefsOpen] = useState(false)
  const prefsRef = useRef<HTMLDivElement>(null)

  const loadProfile = useCallback(() => {
    if (!user) { setLoading(false); return }
    setLoading(true)
    getUserProfile(user.user_id)
      .then((p) => { setProfile(p || {}); setLoading(false) })
      .catch(() => setLoading(false))
  }, [user])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (prefsRef.current && !prefsRef.current.contains(e.target as Node)) {
        setPrefsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const p = (key: string, fallback = '') => (profile[key] as string | number | null) ?? fallback

  const updateField = (key: string, value: string | number) => {
    setProfile((prev) => ({ ...prev, [key]: value }))
    setDirty(true)
  }

  const addItem = (key: string, value: string) => {
    const trimmed = value.trim()
    if (!trimmed) return
    const current = (profile[key] as string[]) || []
    if (current.includes(trimmed)) return
    setProfile((prev) => ({ ...prev, [key]: [...current, trimmed] }))
    setDirty(true)
  }

  const removeItem = (key: string, item: string) => {
    const current = (profile[key] as string[]) || []
    setProfile((prev) => ({ ...prev, [key]: current.filter((x) => x !== item) }))
    setDirty(true)
  }

  const togglePref = (pref: string) => {
    const current = (profile.dietary_preferences as string[]) || []
    const next = current.includes(pref)
      ? current.filter((x) => x !== pref)
      : [...current, pref]
    setProfile((prev) => ({ ...prev, dietary_preferences: next }))
    setDirty(true)
  }

  const handleSave = async () => {
    if (!user) return
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {}
      for (const [key, value] of Object.entries(profile)) {
        if (['daily_calorie_target', 'meals_per_day', 'age', 'budget', 'weight_kg', 'target_weight_kg', 'height_cm'].includes(key)) {
          payload[key] = value != null && value !== '' ? Number(value) : null
        } else {
          payload[key] = value
        }
      }
      const res = await saveProfile(user.user_id, payload)
      if (res.success) {
        setDirty(false)
        loadProfile()
      }
    } catch { /* ignore */ }
    setSaving(false)
  }

  const displayGoal = mapDisplay(p('goal') as string, GOAL_REVERSE)
  const displayActivity = mapDisplay(p('activity_level') as string, ACTIVITY_REVERSE)

  const weight = Number(p('weight_kg')) || 0
  const height = Number(p('height_cm')) || 0
  const bmi = weight > 0 && height > 0 ? weight / ((height / 100) * (height / 100)) : 0

  const goalEmojis: Record<string, string> = {
    'Weight Loss': '\u2696\uFE0F',
    'Weight Gain': '\u{1F3CB}',
    'Maintain Muscle': '\u{1F4AA}',
    'General Health': '\u{1F331}',
    'High Protein': '\u{1F969}',
  }

  const bmiCategory = bmi > 0
    ? bmi < 18.5 ? 'Underweight'
    : bmi < 25 ? 'Normal'
    : bmi < 30 ? 'Overweight'
    : 'Obese'
    : ''

  const bmiColor = bmi > 0
    ? bmi < 18.5 ? 'text-blue'
    : bmi < 25 ? 'text-primary'
    : bmi < 30 ? 'text-warning'
    : 'text-error'
    : ''

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="h-9 w-32 rounded-lg bg-surface animate-shimmer" />
            <div className="h-5 w-64 rounded bg-surface animate-shimmer mt-2" />
          </div>
          <div className="flex gap-3">
            <div className="h-12 w-32 rounded-xl bg-surface animate-shimmer" />
            <div className="h-12 w-32 rounded-xl bg-surface animate-shimmer" />
          </div>
        </div>
        <div className="p-6 rounded-2xl bg-surface border border-border animate-shimmer">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-background" />
            <div className="space-y-3 flex-1">
              <div className="h-6 w-40 rounded bg-background" />
              <div className="flex gap-2">
                <div className="h-6 w-24 rounded-full bg-background" />
                <div className="h-6 w-24 rounded-full bg-background" />
                <div className="h-6 w-24 rounded-full bg-background" />
              </div>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {[1, 2].map((i) => (
              <div key={i} className="p-6 rounded-2xl bg-surface border border-border animate-shimmer">
                <div className="h-6 w-48 rounded bg-background mb-6" />
                <div className="grid grid-cols-2 gap-4">
                  {[1, 2, 3, 4].map((j) => (
                    <div key={j} className="h-20 rounded-xl bg-background" />
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="space-y-6">
            {[1, 2].map((i) => (
              <div key={i} className="p-6 rounded-2xl bg-surface border border-border animate-shimmer">
                <div className="h-6 w-36 rounded bg-background mb-6" />
                <div className="space-y-4">
                  {[1, 2, 3].map((j) => (
                    <div key={j} className="h-12 rounded-xl bg-background" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const allergies = (profile.allergies as string[]) || []
  const favoriteFoods = (profile.favorite_foods as string[]) || []
  const dislikedFoods = (profile.disliked_foods as string[]) || []
  const dietaryPrefs = (profile.dietary_preferences as string[]) || []

  const renderTagSection = (
    label: string,
    items: string[],
    showInput: boolean,
    setShowInput: (v: boolean) => void,
    inputValue: string,
    setInputValue: (v: string) => void,
    addKey: string,
    chipClass: string,
  ) => (
    <div>
      <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">{label}</p>
      <div className="flex flex-wrap items-center gap-2">
        {items.length === 0 && !showInput && <span className="text-xs text-text-muted">None set</span>}
        {items.map((item) => (
          <span key={item} className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-medium ${chipClass}`}>
            {item}
            <button onClick={() => removeItem(addKey, item)} className="hover:opacity-70 transition-opacity">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        {!showInput ? (
          <button
            onClick={() => setShowInput(true)}
            className="w-7 h-7 rounded-full bg-surface-variant hover:bg-border flex items-center justify-center transition-colors"
          >
            <Plus className="w-4 h-4 text-text-muted" />
          </button>
        ) : (
          <div className="flex items-center gap-1.5">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  addItem(addKey, inputValue)
                  setInputValue('')
                  setShowInput(false)
                }
                if (e.key === 'Escape') {
                  setInputValue('')
                  setShowInput(false)
                }
              }}
              autoFocus
              placeholder="Add..."
              className="w-28 px-2.5 py-1.5 rounded-lg bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            />
            <button
              onClick={() => {
                addItem(addKey, inputValue)
                setInputValue('')
                setShowInput(false)
              }}
              className="w-7 h-7 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold hover:bg-primary/90 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => { setInputValue(''); setShowInput(false) }}
              className="w-7 h-7 rounded-full bg-surface-variant hover:bg-border flex items-center justify-center text-xs text-text-muted transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-text tracking-tight">Profile</h1>
          <p className="text-sm text-text-secondary mt-1.5">Manage your health profile and dietary preferences.</p>
        </div>
        <div className="hidden sm:flex items-center gap-3">
          <Button
            variant="outline"
            size="lg"
            className="h-12 rounded-xl"
            onClick={() => { loadProfile(); setDirty(false) }}
          >
            Reset
          </Button>
          <Button
            variant="primary"
            size="lg"
            className="h-12 rounded-xl bg-gradient-to-r from-primary to-emerald-400 shadow-md shadow-primary/20"
            onClick={handleSave}
            disabled={!dirty || saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {/* Profile Overview */}
      <div className="p-6 rounded-2xl bg-surface border border-border">
        <div className="flex flex-wrap items-center gap-5">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-3xl shrink-0">
            {'\u{1F464}'}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-bold text-text">
              {user?.email?.split('@')[0] || 'User'}
            </h2>
            <div className="flex flex-wrap items-center gap-2 mt-2.5">
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium">
                <Target className="w-3 h-3" />
                {displayGoal || 'No Goal'}
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue/10 text-blue text-xs font-medium">
                <Activity className="w-3 h-3" />
                {displayActivity || 'N/A'}
              </span>
              {bmi > 0 && (
                <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${bmiColor} bg-current/10`}>
                  BMI {bmi.toFixed(1)}
                </span>
              )}
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-warning/10 text-warning text-xs font-medium">
                <Flame className="w-3 h-3" />
                {p('daily_calorie_target') || '--'} kcal/day
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Information */}
          <div className="p-6 rounded-2xl bg-surface border border-border">
            <h2 className="text-lg font-semibold text-text mb-6">Personal Information</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Weight */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Scale className="w-4 h-4 text-text-muted" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Current Weight</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <input
                    type="number"
                    value={p('weight_kg')}
                    onChange={(e) => updateField('weight_kg', Number(e.target.value))}
                    className="w-20 bg-transparent text-xl font-bold text-text focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                  <span className="text-sm text-text-secondary">kg</span>
                </div>
              </div>
              {/* Target Weight */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Scale className="w-4 h-4 text-text-muted" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Target Weight</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <input
                    type="number"
                    value={p('target_weight_kg')}
                    onChange={(e) => updateField('target_weight_kg', Number(e.target.value))}
                    className="w-20 bg-transparent text-xl font-bold text-text focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                  <span className="text-sm text-text-secondary">kg</span>
                </div>
              </div>
              {/* Height */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Ruler className="w-4 h-4 text-text-muted" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Height</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <input
                    type="number"
                    value={p('height_cm')}
                    onChange={(e) => updateField('height_cm', Number(e.target.value))}
                    className="w-20 bg-transparent text-xl font-bold text-text focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                  <span className="text-sm text-text-secondary">cm</span>
                </div>
              </div>
              {/* Age */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Cake className="w-4 h-4 text-text-muted" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Age</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <input
                    type="number"
                    value={p('age')}
                    onChange={(e) => updateField('age', Number(e.target.value))}
                    className="w-20 bg-transparent text-xl font-bold text-text focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                  <span className="text-sm text-text-secondary">years</span>
                </div>
              </div>
              {/* Gender */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Cake className="w-4 h-4 text-text-muted" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Gender</span>
                </div>
                <input
                  type="text"
                  value={p('gender')}
                  onChange={(e) => updateField('gender', e.target.value)}
                  placeholder="e.g. Male, Female"
                  className="w-full bg-transparent text-base font-semibold text-text focus:outline-none placeholder:text-text-muted"
                />
              </div>
              {/* Activity Level */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-text-muted" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Activity Level</span>
                </div>
                <select
                  value={displayActivity}
                  onChange={(e) => updateField('activity_level', e.target.value)}
                  className="w-full bg-transparent text-base font-semibold text-text focus:outline-none cursor-pointer"
                >
                  <option value="" className="bg-surface">Select...</option>
                  {ACTIVITY_LEVELS.map((opt) => (
                    <option key={opt} value={opt} className="bg-surface">{opt}</option>
                  ))}
                </select>
              </div>
              {/* Daily Calories */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Flame className="w-4 h-4 text-warning" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Daily Calories</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <input
                    type="number"
                    value={p('daily_calorie_target')}
                    onChange={(e) => updateField('daily_calorie_target', Number(e.target.value))}
                    className="w-24 bg-transparent text-xl font-bold text-text focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                  <span className="text-sm text-text-secondary">kcal</span>
                </div>
              </div>
              {/* Meals Per Day */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <UtensilsCrossed className="w-4 h-4 text-blue" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Meals Per Day</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <input
                    type="number"
                    value={p('meals_per_day', '3')}
                    onChange={(e) => updateField('meals_per_day', Number(e.target.value))}
                    min={1}
                    max={10}
                    className="w-16 bg-transparent text-xl font-bold text-text focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                  <span className="text-sm text-text-secondary">meals</span>
                </div>
              </div>
              {/* Budget */}
              <div className="p-4 rounded-xl bg-background border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Wallet className="w-4 h-4 text-purple" />
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Weekly Budget</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-sm text-text-secondary">$</span>
                  <input
                    type="number"
                    value={p('budget')}
                    onChange={(e) => updateField('budget', Number(e.target.value))}
                    className="w-20 bg-transparent text-xl font-bold text-text focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                  <span className="text-sm text-text-secondary">/wk</span>
                </div>
              </div>
            </div>

            {/* Goals */}
            <div className="mt-6">
              <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">Goal</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {GOALS.map((g) => {
                  const selected = displayGoal === g
                  return (
                    <button
                      key={g}
                      onClick={() => updateField('goal', g)}
                      className={`p-4 rounded-xl border-2 text-left transition-all duration-200 ${
                        selected
                          ? 'border-primary bg-primary/10 shadow-sm shadow-primary/20'
                          : 'border-border bg-background hover:border-primary/50 hover:bg-surface-variant'
                      }`}
                    >
                      <span className="text-2xl">{goalEmojis[g] || '\u{1F331}'}</span>
                      <p className={`text-sm font-medium mt-1.5 ${selected ? 'text-primary' : 'text-text'}`}>
                        {g}
                      </p>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Dietary Preferences */}
          <div className="p-6 rounded-2xl bg-surface border border-border">
            <h2 className="text-lg font-semibold text-text mb-6">Dietary Preferences</h2>
            <div className="space-y-6">
              {renderTagSection('Allergies', allergies, showAllergyInput, setShowAllergyInput, newAllergy, setNewAllergy, 'allergies', 'bg-error/10 text-error')}
              {renderTagSection('Favorite Foods', favoriteFoods, showFavoriteInput, setShowFavoriteInput, newFavorite, setNewFavorite, 'favorite_foods', 'bg-primary/10 text-primary')}
              {renderTagSection('Disliked Foods', dislikedFoods, showDislikedInput, setShowDislikedInput, newDisliked, setNewDisliked, 'disliked_foods', 'bg-surface-variant text-text-secondary')}

              <div ref={prefsRef} className="relative">
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">Dietary Preferences</p>
                <button
                  onClick={() => setPrefsOpen(!prefsOpen)}
                  className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text hover:bg-surface-variant transition-colors"
                >
                  <span className={dietaryPrefs.length === 0 ? 'text-text-muted' : ''}>
                    {dietaryPrefs.length > 0 ? dietaryPrefs.join(', ') : 'Select preferences...'}
                  </span>
                  <ChevronDown className={`w-4 h-4 text-text-muted transition-transform ${prefsOpen ? 'rotate-180' : ''}`} />
                </button>
                {prefsOpen && (
                  <div className="absolute z-10 mt-1 w-full rounded-xl bg-surface border border-border shadow-lg overflow-hidden">
                    {DIETARY_PREFS.map((d) => {
                      const selected = dietaryPrefs.includes(d)
                      return (
                        <button
                          key={d}
                          onClick={() => togglePref(d)}
                          className={cn(
                            'w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left hover:bg-surface-variant transition-colors',
                            selected ? 'text-text font-medium' : 'text-text-secondary'
                          )}
                        >
                          <span className={cn(
                            'w-4 h-4 rounded border-2 flex items-center justify-center shrink-0',
                            selected ? 'bg-primary border-primary' : 'border-border'
                          )}>
                            {selected && <Check className="w-3 h-3 text-white" />}
                          </span>
                          {d}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Health Summary */}
          <div className="p-6 rounded-2xl bg-surface border border-border">
            <h2 className="text-lg font-semibold text-text mb-6">Health Summary</h2>
            <div className="space-y-5">
              {/* BMI */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-text-muted" />
                    <span className="text-sm text-text-secondary">BMI</span>
                  </div>
                  <span className={`text-sm font-semibold ${bmiColor}`}>
                    {bmi > 0 ? bmi.toFixed(1) : '--'}
                  </span>
                </div>
                {bmi > 0 && (
                  <div className="h-1.5 bg-secondary/20 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        bmi < 18.5 ? 'bg-blue'
                        : bmi < 25 ? 'bg-primary'
                        : bmi < 30 ? 'bg-warning'
                        : 'bg-error'
                      }`}
                      style={{ width: `${Math.min((bmi / 40) * 100, 100)}%` }}
                    />
                  </div>
                )}
                {bmiCategory && (
                  <p className="text-xs text-text-muted mt-1">{bmiCategory}</p>
                )}
              </div>
              {/* Calorie Target */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Flame className="w-4 h-4 text-warning" />
                    <span className="text-sm text-text-secondary">Calories</span>
                  </div>
                  <span className="text-sm font-semibold text-text">
                    {p('daily_calorie_target') || '--'} <span className="text-text-muted font-normal">kcal</span>
                  </span>
                </div>
                <p className="text-xs text-text-muted">Daily target</p>
              </div>
              {/* Meals */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <UtensilsCrossed className="w-4 h-4 text-blue" />
                    <span className="text-sm text-text-secondary">Meals</span>
                  </div>
                  <span className="text-sm font-semibold text-text">
                    {p('meals_per_day', '3')} <span className="text-text-muted font-normal">/ day</span>
                  </span>
                </div>
                <p className="text-xs text-text-muted">Planned meals</p>
              </div>
              {/* Budget */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Wallet className="w-4 h-4 text-purple" />
                    <span className="text-sm text-text-secondary">Budget</span>
                  </div>
                  <span className="text-sm font-semibold text-text">
                    {p('budget') ? `$${p('budget')}` : '--'} <span className="text-text-muted font-normal">/ wk</span>
                  </span>
                </div>
                <p className="text-xs text-text-muted">Weekly spending</p>
              </div>
              {/* Goal */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-primary" />
                    <span className="text-sm text-text-secondary">Goal</span>
                  </div>
                  <span className="text-sm font-semibold text-text">{displayGoal || 'Not set'}</span>
                </div>
                <p className="text-xs text-text-muted">Current nutrition strategy</p>
              </div>
            </div>
          </div>

          {/* AI Recommendation */}
          <div className="p-6 rounded-2xl bg-surface border border-border">
            <h2 className="text-lg font-semibold text-text mb-4">AI Recommendation</h2>
            <p className="text-sm text-text-secondary leading-relaxed mb-4">
              Based on your profile, we tailor meal plans to support your <span className="text-text font-medium">{displayGoal || 'nutrition'}</span> goal.
            </p>
            <div className="flex flex-wrap gap-2">
              {displayGoal && (
                <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-primary/10 text-primary text-xs font-medium">
                  {displayGoal}
                </span>
              )}
              <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-blue/10 text-blue text-xs font-medium">
                Meal Prep
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-warning/10 text-warning text-xs font-medium">
                Budget Friendly
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-primary/10 text-primary text-xs font-medium">
                Healthy
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Save/Reset */}
      <div className="flex sm:hidden justify-end gap-3">
        <Button
          variant="outline"
          size="lg"
          className="h-12 rounded-xl"
          onClick={() => { loadProfile(); setDirty(false) }}
        >
          Reset
        </Button>
        <Button
          variant="primary"
          size="lg"
          className="h-12 rounded-xl bg-gradient-to-r from-primary to-emerald-400 shadow-md shadow-primary/20"
          onClick={handleSave}
          disabled={!dirty || saving}
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </div>
  )
}
