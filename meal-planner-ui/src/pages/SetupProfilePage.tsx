import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Loader2, ChevronRight, ChevronLeft, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { saveUserProfile } from '@/lib/api'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'

const GOALS = ['Weight Loss', 'Weight Gain', 'Maintain Muscle', 'General Health', 'High Protein']
const ACTIVITY_LEVELS = ['Sedentary', 'Light', 'Moderate', 'Active', 'Very Active']
const DIETARY_PREFS = ['No Preference', 'Vegetarian', 'Vegan', 'Keto', 'Paleo', 'Mediterranean', 'Low Carb']

export function SetupProfilePage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)

  const [step, setStep] = useState(1)
  const [saving, setSaving] = useState(false)

  const [profile, setProfile] = useState({
    age: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    target_weight_kg: '',
    activity_level: 'Moderate',
    goal: 'General Health',
    meals_per_day: '3',
    daily_calorie_target: '',
    budget: '',
    dietary_preferences: [] as string[],
    favorite_foods: '',
    disliked_foods: '',
    allergies: '',
  })

  const update = (key: string, value: string) => setProfile((p) => ({ ...p, [key]: value }))

  const togglePref = (pref: string) => {
    setProfile((p) => ({
      ...p,
      dietary_preferences: p.dietary_preferences.includes(pref)
        ? p.dietary_preferences.filter((x) => x !== pref)
        : [...p.dietary_preferences, pref],
    }))
  }

  const handleSave = async () => {
    if (!user) return
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        age: Number(profile.age) || null,
        gender: profile.gender,
        height_cm: Number(profile.height_cm) || null,
        weight_kg: Number(profile.weight_kg) || null,
        target_weight_kg: Number(profile.target_weight_kg) || null,
        activity_level: profile.activity_level,
        goal: profile.goal,
        meals_per_day: Number(profile.meals_per_day) || 3,
        daily_calorie_target: Number(profile.daily_calorie_target) || null,
        budget: Number(profile.budget) || null,
        dietary_preferences: profile.dietary_preferences.filter((p) => p !== 'No Preference'),
        favorite_foods: profile.favorite_foods.split(',').map((s) => s.trim()).filter(Boolean),
        disliked_foods: profile.disliked_foods.split(',').map((s) => s.trim()).filter(Boolean),
        allergies: profile.allergies.split(',').map((s) => s.trim()).filter(Boolean),
      }
      await saveUserProfile(user.user_id, payload)
      setUser({ ...user, profile_complete: true })
      navigate('/dashboard', { replace: true })
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-lg">
        <div className="rounded-2xl bg-surface border border-border p-8 shadow-xl shadow-black/20">
          <div className="text-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-6 h-6 text-on-primary" />
            </div>
            <h1 className="text-xl font-bold text-text">Set Up Your Profile</h1>
            <p className="text-sm text-text-muted mt-1">Tell us about yourself so we can personalize your meal plans</p>
          </div>

          <div className="flex items-center justify-center gap-2 mb-8">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
                    step === s && 'bg-primary text-on-primary',
                    step > s && 'bg-primary/20 text-primary',
                    step < s && 'bg-surface-variant text-text-muted'
                  )}
                >
                  {step > s ? <Check className="w-4 h-4" /> : s}
                </div>
                {s < 3 && <div className={cn('w-8 h-0.5 rounded', step > s ? 'bg-primary' : 'bg-border')} />}
              </div>
            ))}
          </div>

          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold text-text">Basic Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Age</label>
                  <input type="number" value={profile.age} onChange={(e) => update('age', e.target.value)} placeholder="30" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Gender</label>
                  <select value={profile.gender} onChange={(e) => update('gender', e.target.value)} className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
                    <option value="">Select...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Height (cm)</label>
                  <input type="number" value={profile.height_cm} onChange={(e) => update('height_cm', e.target.value)} placeholder="175" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Weight (kg)</label>
                  <input type="number" value={profile.weight_kg} onChange={(e) => update('weight_kg', e.target.value)} placeholder="70" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Target Weight (kg)</label>
                <input type="number" value={profile.target_weight_kg} onChange={(e) => update('target_weight_kg', e.target.value)} placeholder="65" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold text-text">Goals & Preferences</h2>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Goal</label>
                <div className="grid grid-cols-2 gap-2">
                  {GOALS.map((g) => (
                    <button key={g} onClick={() => update('goal', g)} className={cn('px-4 py-2.5 rounded-xl text-sm font-medium border transition-colors cursor-pointer text-left', profile.goal === g ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:bg-surface-variant text-text-secondary')}>
                      {g}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Activity Level</label>
                <div className="grid grid-cols-2 gap-2">
                  {ACTIVITY_LEVELS.map((a) => (
                    <button key={a} onClick={() => update('activity_level', a)} className={cn('px-4 py-2.5 rounded-xl text-sm font-medium border transition-colors cursor-pointer text-left', profile.activity_level === a ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:bg-surface-variant text-text-secondary')}>
                      {a}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Dietary Preferences</label>
                <div className="flex flex-wrap gap-2">
                  {DIETARY_PREFS.map((d) => (
                    <button key={d} onClick={() => togglePref(d)} className={cn('px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer', profile.dietary_preferences.includes(d) ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:bg-surface-variant text-text-secondary')}>
                      {d}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Meals / Day</label>
                  <input type="number" value={profile.meals_per_day} onChange={(e) => update('meals_per_day', e.target.value)} min={1} max={6} className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Daily Calorie Target</label>
                  <input type="number" value={profile.daily_calorie_target} onChange={(e) => update('daily_calorie_target', e.target.value)} placeholder="2000" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Budget ($/week)</label>
                <input type="number" value={profile.budget} onChange={(e) => update('budget', e.target.value)} placeholder="100" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold text-text">Food Preferences</h2>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Favorite Foods (comma separated)</label>
                <input type="text" value={profile.favorite_foods} onChange={(e) => update('favorite_foods', e.target.value)} placeholder="Chicken, Rice, Vegetables" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Disliked Foods (comma separated)</label>
                <input type="text" value={profile.disliked_foods} onChange={(e) => update('disliked_foods', e.target.value)} placeholder="Fish, Tofu" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Allergies (comma separated)</label>
                <input type="text" value={profile.allergies} onChange={(e) => update('allergies', e.target.value)} placeholder="Peanuts, Shrimp, Dairy" className="w-full px-4 py-2.5 rounded-xl bg-background border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
              </div>
            </div>
          )}

          <div className="flex justify-between mt-8">
            {step > 1 ? (
              <Button variant="outline" onClick={() => setStep(step - 1)}>
                <ChevronLeft className="w-4 h-4" />
                Back
              </Button>
            ) : (
              <div />
            )}
            {step < 3 ? (
              <Button onClick={() => setStep(step + 1)}>
                Next
                <ChevronRight className="w-4 h-4" />
              </Button>
            ) : (
              <Button onClick={handleSave} disabled={saving}>
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                {saving ? 'Saving...' : 'Complete Setup'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
