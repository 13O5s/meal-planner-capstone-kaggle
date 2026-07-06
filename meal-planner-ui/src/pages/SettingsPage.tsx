import { useState } from 'react'
import { Sun, Moon, Bell } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { useThemeStore } from '@/stores/theme-store'
import { cn } from '@/lib/utils'

const tabs = ['Theme', 'Notifications']

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('Theme')
  const { isDark, toggle } = useThemeStore()

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-text">Settings</h1>
        <p className="text-text-secondary mt-1.5 text-sm">Customize your experience.</p>
      </div>

      <div className="flex gap-1 flex-wrap mb-8 border-b border-border pb-0">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-[1px] cursor-pointer',
              activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-text-muted hover:text-text'
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Theme' && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              {isDark ? <Moon className="w-5 h-5 text-text" /> : <Sun className="w-5 h-5 text-text" />}
              <h2 className="text-lg font-semibold text-text">Theme</h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex gap-4">
              <button
                onClick={() => { if (isDark) toggle() }}
                className={cn(
                  'flex-1 p-6 rounded-xl border-2 text-center transition-all cursor-pointer',
                  !isDark
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                )}
              >
                <Sun className="w-8 h-8 mx-auto mb-2 text-text" />
                <p className="text-sm font-medium text-text">Light</p>
              </button>
              <button
                onClick={() => { if (!isDark) toggle() }}
                className={cn(
                  'flex-1 p-6 rounded-xl border-2 text-center transition-all cursor-pointer',
                  isDark
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                )}
              >
                <Moon className="w-8 h-8 mx-auto mb-2 text-text" />
                <p className="text-sm font-medium text-text">Dark</p>
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'Notifications' && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-text" />
              <h2 className="text-lg font-semibold text-text">Notifications</h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: 'Meal plan ready', desc: 'When a new meal plan is generated', key: 'meal_plan_ready' },
              { label: 'Budget update', desc: 'When shopping list exceeds your budget', key: 'budget_update' },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                <div>
                  <p className="text-sm font-medium text-text">{item.label}</p>
                  <p className="text-xs text-text-muted mt-0.5">{item.desc}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked className="sr-only peer" />
                  <div className="w-11 h-6 rounded-full bg-surface-variant peer-checked:bg-primary after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-5 after:h-5 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-5" />
                </label>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
