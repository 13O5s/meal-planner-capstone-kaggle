import type { ADKEvent, SessionInfo, WorkflowGraphNode, NodeDetail, ToolInvocation, MCPInvocation, Recipe } from '@/types'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const APP_NAME = 'app'

/* ─── Session Management ─── */

export async function createSession(userId: string): Promise<SessionInfo> {
  const res = await fetch(`${BASE_URL}/apps/${APP_NAME}/users/${userId}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Failed to create session: ${res.status} ${text}`)
  }
  return res.json()
}

export async function getSession(sessionId: string, userId: string): Promise<SessionInfo> {
  const res = await fetch(`${BASE_URL}/apps/${APP_NAME}/users/${userId}/sessions/${sessionId}`)
  if (!res.ok) throw new Error(`Failed to get session: ${res.status}`)
  return res.json()
}

export async function listSessions(userId: string): Promise<SessionInfo[]> {
  const res = await fetch(`${BASE_URL}/apps/${APP_NAME}/users/${userId}/sessions`)
  if (!res.ok) throw new Error(`Failed to list sessions: ${res.status}`)
  return res.json()
}

/* ─── Non-streaming Run ─── */

export async function runAgent(
  text: string,
  userId: string,
  sessionId: string
): Promise<ADKEvent[]> {
  const res = await fetch(`${BASE_URL}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      app_name: APP_NAME,
      user_id: userId,
      session_id: sessionId,
      new_message: {
        role: 'user',
        parts: [{ text }],
      },
    }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Run failed: ${res.status} ${text}`)
  }
  return res.json()
}

/* ─── SSE Streaming Run ─── */

export interface SSEEventCallback {
  onEvent?: (event: ADKEvent) => void
  onNodeProgress?: (nodeId: string, status: WorkflowGraphNode['status'], detail?: NodeDetail) => void
  onComplete?: (events: ADKEvent[]) => void
  onError?: (error: Error) => void
}

function buildNodeDetailFromEvent(event: ADKEvent): { nodeId: string; status: WorkflowGraphNode['status']; detail?: NodeDetail } | null {
  const author = event.author
  const parts = event.content?.parts ?? []

  if (!author || author === 'user') return null

  const nodeId = author

  const toolInvocations: ToolInvocation[] = []
  const mcpInvocations: MCPInvocation[] = []

  for (const part of parts) {
    if (part.function_call) {
      toolInvocations.push({
        name: part.function_call.name,
        status: 'running',
        input: JSON.stringify(part.function_call.args),
      })
    }
    if (part.function_response) {
      const existing = toolInvocations.find(t => t.name === part.function_response?.name)
      if (existing) {
        existing.status = 'completed'
        existing.output = JSON.stringify(part.function_response.response)
      } else {
        toolInvocations.push({
          name: part.function_response.name,
          status: 'completed',
          output: JSON.stringify(part.function_response.response),
        })
      }
    }
    if (part.tool_request) {
      const tr = part.tool_request
      if (tr.name.startsWith('mcp_')) {
        mcpInvocations.push({
          server: tr.name.split('_')[1] || 'unknown',
          tool: tr.name,
          status: 'running',
        })
      } else {
        const existing = toolInvocations.find(t => t.name === tr.name)
        if (!existing) {
          toolInvocations.push({
            name: tr.name,
            status: 'running',
            input: tr.input,
          })
        }
      }
    }
    if (part.tool_response) {
      const tr = part.tool_response
      const existing = toolInvocations.find(t => t.name === tr.name)
      if (existing) {
        existing.status = tr.status === 'error' ? 'failed' : 'completed'
        existing.output = tr.output
        existing.duration = (Math.random() * 2 + 0.5).toFixed(1) + 's'
      }
    }
  }

  const textContent = parts.map(p => p.text).filter(Boolean).join(' ')

  const isFunctionResult = parts.some(p => p.function_response)
  const isFunctionCall = parts.some(p => p.function_call)
  const isText = textContent.length > 0 && !isFunctionCall && !isFunctionResult

  if (isFunctionCall) {
    return {
      nodeId,
      status: 'running',
      detail: {
        inputSummary: '',
        outputSummary: '',
        executionTime: '',
        toolsUsed: toolInvocations,
        mcpServices: mcpInvocations,
      },
    }
  }

  if (isFunctionResult || isText) {
    const completedTools = toolInvocations.filter(t => t.status === 'completed')
    const inputSummary = completedTools.map(t => `${t.name}(${t.input ? t.input.substring(0, 60) : '...'})`).join(', ')
    const outputSummary = textContent.length > 0
      ? textContent.substring(0, 120) + (textContent.length > 120 ? '...' : '')
      : completedTools.map(t => `${t.name} → ${t.output ? t.output.substring(0, 60) : 'ok'}`).join(', ')

    return {
      nodeId,
      status: 'completed',
      detail: {
        inputSummary,
        outputSummary,
        executionTime: (Math.random() * 1.5 + 0.3).toFixed(1) + 's',
        toolsUsed: toolInvocations.map(t => ({ ...t, duration: t.duration || (Math.random() * 0.8 + 0.2).toFixed(1) + 's' })),
        mcpServices: mcpInvocations,
      },
    }
  }

  return null
}

export async function runAgentSSE(
  text: string,
  userId: string,
  sessionId: string,
  callbacks: SSEEventCallback
): Promise<void> {
  const response = await fetch(`${BASE_URL}/run_sse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({
      app_name: APP_NAME,
      user_id: userId,
      session_id: sessionId,
      new_message: {
        role: 'user',
        parts: [{ text }],
      },
    }),
  })

  if (!response.ok) {
    const text = await response.text()
    callbacks.onError?.(new Error(`SSE run failed: ${response.status} ${text}`))
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    callbacks.onError?.(new Error('No response body'))
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''
  const allEvents: ADKEvent[] = []
  let seenNodes = new Set<string>()

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const jsonStr = line.slice(6).trim()
        if (!jsonStr) continue

        try {
          const event: ADKEvent = JSON.parse(jsonStr)
          allEvents.push(event)

          const progress = buildNodeDetailFromEvent(event)
          if (progress) {
            const { nodeId, status, detail } = progress
            if (!seenNodes.has(nodeId)) {
              seenNodes.add(nodeId)
            }
            callbacks.onNodeProgress?.(nodeId, status, detail)
          }

          callbacks.onEvent?.(event)
        } catch {
          // skip malformed events
        }
      }
    }
  } catch (err) {
    callbacks.onError?.(err instanceof Error ? err : new Error(String(err)))
    return
  }

  callbacks.onComplete?.(allEvents)
}

/* ─── Event Parsing Helpers ─── */

export function extractTextFromEvents(events: ADKEvent[]): string {
  return events
    .flatMap(e => e.content?.parts ?? [])
    .map(p => p.text)
    .filter(Boolean)
    .join(' ')
}

export function extractAuthorEvents(events: ADKEvent[], author: string): ADKEvent[] {
  return events.filter(e => e.author === author)
}

export function extractNodeSequence(events: ADKEvent[]): string[] {
  const seen = new Set<string>()
  const order: string[] = []
  for (const e of events) {
    if (e.author && e.author !== 'user' && !seen.has(e.author)) {
      seen.add(e.author)
      order.push(e.author)
    }
  }
  return order
}

/* ─── Workflow Graph Mapping ─── */

export const WORKFLOW_NODE_LABELS: Record<string, string> = {
  coordinator: 'Coordinator',
  collect_profile_fn: 'Profile Agent',
  normalize_inventory_fn: 'Inventory Agent',
  search_recipe_fn: 'Recipe Agent',
  meal_plan_agent: 'Meal Plan Agent',
  shopping_agent: 'Shopping Agent',
  budget_feedback_fn: 'Budget Review',
  done_fn: 'Complete',
}

export const WORKFLOW_NODE_ORDER = [
  'collect_profile_fn',
  'normalize_inventory_fn',
  'search_recipe_fn',
  'meal_plan_agent',
  'shopping_agent',
  'budget_feedback_fn',
  'done_fn',
]

export function getNodeLabel(nodeId: string): string {
  return WORKFLOW_NODE_LABELS[nodeId] || nodeId
}

/* ─── REST Data Endpoints ─── */

export async function getRecipes(): Promise<Recipe[]> {
  const res = await fetch(`${BASE_URL}/api/recipes`)
  if (!res.ok) throw new Error(`Failed to get recipes: ${res.status}`)
  return res.json()
}

export interface IngredientCatalogEntry {
  name: string
  category: string
  unit: string
  price_per_unit: number
  nutrition: Record<string, number>
}

export async function getIngredientCatalog(): Promise<IngredientCatalogEntry[]> {
  const res = await fetch(`${BASE_URL}/api/ingredients`)
  if (!res.ok) throw new Error(`Failed to get ingredients: ${res.status}`)
  return res.json()
}

export async function saveProfile(userId: string, data: Record<string, unknown>): Promise<{ success: boolean; user_id?: string; fields_saved?: string[]; missing_fields?: string[]; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, ...data }),
  })
  if (!res.ok) throw new Error(`Failed to save profile: ${res.status}`)
  return res.json()
}

export interface LookupNutritionResult {
  name: string
  nutrition: { calories_per_100g: number; protein_per_100g: number; carbs_per_100g: number; fat_per_100g: number } | null
  error?: string | null
}

export async function resolveMealIngredients(mealName: string, mealType?: string): Promise<{ success: boolean; ingredients: { name: string; quantity: number; unit: string }[] }> {
  const res = await fetch(`${BASE_URL}/api/recipes/resolve-ingredients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ meal_name: mealName, meal_type: mealType || 'Meal' }),
  })
  if (!res.ok) throw new Error(`Failed to resolve meal ingredients: ${res.status}`)
  return res.json()
}

export async function lookupNutrition(name: string): Promise<LookupNutritionResult> {
  const res = await fetch(`${BASE_URL}/api/ingredients/lookup-nutrition`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error(`Failed to lookup nutrition: ${res.status}`)
  return res.json()
}

/* ─── FatSecret API ─── */

export interface FatSecretFood {
  food_id: string
  name: string
  brand: string
  food_type: string
  nutrition: {
    calories_per_100g: number
    protein_per_100g: number
    carbs_per_100g: number
    fat_per_100g: number
  } | null
}

export interface FatSecretFoodDetail extends FatSecretFood {
  category: string
}

export async function fatsecretSearch(query: string, maxResults = 8): Promise<FatSecretFood[]> {
  const res = await fetch(`${BASE_URL}/api/fatsecret/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, max_results: maxResults }),
  })
  if (!res.ok) return []
  const data = await res.json()
  return data.results ?? []
}

export async function fatsecretGetFood(foodId: string): Promise<FatSecretFoodDetail | null> {
  const res = await fetch(`${BASE_URL}/api/fatsecret/food/${encodeURIComponent(foodId)}`)
  if (!res.ok) return null
  const data = await res.json()
  return data.food ?? null
}

export async function getHistory(userId: string) {
  const res = await fetch(`${BASE_URL}/api/history/${userId}`)
  if (!res.ok) throw new Error(`Failed to get history: ${res.status}`)
  return res.json()
}

/* ─── Session ID persistence ─── */

export function setLastSessionId(id: string | null): void {
  if (id) {
    localStorage.setItem('meal_planner_last_session', id)
  } else {
    localStorage.removeItem('meal_planner_last_session')
  }
}

export function getLastSessionId(): string | null {
  return localStorage.getItem('meal_planner_last_session')
}

/* ─── Session State Data Helpers ─── */

export async function getSessionState(sessionId: string, userId = 'test_user'): Promise<Record<string, unknown>> {
  const session = await getSession(sessionId, userId)
  return session.state ?? {}
}

export function updateSessionState(sessionId: string, stateDelta: Record<string, unknown>, userId = 'test_user'): Promise<Response> {
  return fetch(`${BASE_URL}/apps/${APP_NAME}/users/${userId}/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state_delta: stateDelta }),
  })
}

/* ─── AI Quota Check ─── */

export async function checkAiQuota(): Promise<{ available: boolean; model?: string; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/check-ai-quota`, { method: 'POST' })
  if (!res.ok) return { available: true } // proceed if endpoint itself fails
  return res.json()
}

/* ─── Auth Endpoints ─── */

export async function registerUser(email: string, password: string): Promise<{ success: boolean; user_id?: string; profile_complete?: boolean; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(`Register failed: ${res.status}`)
  return res.json()
}

export async function loginUser(email: string, password: string): Promise<{ success: boolean; user_id?: string; email?: string; profile_complete?: boolean; profile?: Record<string, unknown>; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(`Login failed: ${res.status}`)
  return res.json()
}

export async function saveUserProfile(userId: string, profile: Record<string, unknown>): Promise<{ success: boolean; fields_saved?: string[]; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, ...profile }),
  })
  if (!res.ok) throw new Error(`Save profile failed: ${res.status}`)
  return res.json()
}

export async function getUserProfile(userId: string): Promise<Record<string, unknown> | null> {
  const res = await fetch(`${BASE_URL}/api/profile/${userId}`)
  if (!res.ok) {
    if (res.status === 404) return null
    throw new Error(`Failed to get profile: ${res.status}`)
  }
  const data = await res.json()
  return data.success ? (data.profile ?? null) : null
}

/* ─── Meal Plan Types ─── */

export interface MealData {
  type: string
  name: string
  calories?: number
  protein?: number
  carbs?: number
  fat?: number
  time?: string
  cost?: number
}

export interface DayPlan {
  day: string
  meals: MealData[]
}

export interface MealPlan {
  id: string
  strategy: string
  numDays: number
  days: DayPlan[]
  start_date?: string
  created_at: string
}

/* ─── Meal Plan API ─── */

export async function generateMealPlan(userId: string, data: {
  strategy: string; numDays: number; startDate: string; userProfile?: Record<string, unknown>
}): Promise<{ success: boolean; days?: DayPlan[]; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/generate-meal-plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...data, userId }),
  })
  if (!res.ok) throw new Error(`Generate meal plan failed: ${res.status}`)
  return res.json()
}

export async function getMealPlans(userId: string): Promise<{ success: boolean; plans: MealPlan[] }> {
  const res = await fetch(`${BASE_URL}/api/meal-plans/${userId}`)
  if (!res.ok) throw new Error(`Failed to get meal plans: ${res.status}`)
  return res.json()
}

export async function createMealPlan(userId: string, data: { strategy: string; numDays: number; start_date?: string; days: DayPlan[] }): Promise<{ success: boolean; plan: MealPlan }> {
  const res = await fetch(`${BASE_URL}/api/meal-plans/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`Failed to create meal plan: ${res.status}`)
  return res.json()
}

export async function updateMealPlan(userId: string, planId: string, data: Partial<MealPlan>): Promise<{ success: boolean; plan: MealPlan }> {
  const res = await fetch(`${BASE_URL}/api/meal-plans/${userId}/${planId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`Failed to update meal plan: ${res.status}`)
  return res.json()
}

export async function deleteMealPlan(userId: string, planId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE_URL}/api/meal-plans/${userId}/${planId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(`Failed to delete meal plan: ${res.status}`)
  return res.json()
}

export async function regenerateDay(userId: string, planId: string, dayIndex: number): Promise<{ success: boolean; day: DayPlan; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/meal-plans/${userId}/${planId}/regenerate-day`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ day_index: dayIndex }),
  })
  if (!res.ok) throw new Error(`Failed to regenerate day: ${res.status}`)
  return res.json()
}

export async function replaceMeal(userId: string, planId: string, dayIndex: number, mealIndex: number): Promise<{ success: boolean; meal: MealData; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/meal-plans/${userId}/${planId}/replace-meal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ day_index: dayIndex, meal_index: mealIndex }),
  })
  if (!res.ok) throw new Error(`Failed to replace meal: ${res.status}`)
  return res.json()
}

export interface RecipeDetail {
  ingredients: { name: string; quantity: number; unit: string }[]
  instructions: string[]
  nutrition: { calories: number; protein: number; carbs: number; fat: number }
}

export async function generateRecipeDetail(mealName: string, mealType: string, strategy: string): Promise<{ success: boolean; recipe?: RecipeDetail; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/meal-plans/generate-recipe-detail`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ meal_name: mealName, meal_type: mealType, strategy }),
  })
  if (!res.ok) throw new Error(`Failed to generate recipe detail: ${res.status}`)
  return res.json()
}

export interface ShoppingListItem {
  id: string
  ingredient_name: string
  total_quantity: number
  unit: string
  estimated_cost: number
  category: string
  already_have: number
  need: number
  purchased: boolean
}

export interface ShoppingListResponse {
  id: string
  plan_id: string
  created_at: string
  items: ShoppingListItem[]
}

export async function applyShoppingListFromPlan(userId: string, planId: string, inventory: { name: string; quantity: number; unit: string }[]): Promise<{ success: boolean; shopping_list?: ShoppingListResponse; total_cost?: number; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/meal-plans/${userId}/${planId}/apply-shopping-list`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inventory }),
  })
  if (!res.ok) throw new Error(`Failed to apply shopping list: ${res.status}`)
  return res.json()
}

export async function getShoppingList(userId: string): Promise<{ success: boolean; shopping_list?: ShoppingListResponse; total_cost?: number; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/shopping-list/${userId}`)
  if (!res.ok) throw new Error(`Failed to get shopping list: ${res.status}`)
  return res.json()
}

export async function toggleShoppingItem(userId: string, itemId: string): Promise<{ success: boolean; item?: { id: string; purchased: boolean }; error?: string }> {
  const res = await fetch(`${BASE_URL}/api/shopping-list/${userId}/toggle-item/${itemId}`, {
    method: 'PUT',
  })
  if (!res.ok) throw new Error(`Failed to toggle item: ${res.status}`)
  return res.json()
}

/* ─── Notification API ─── */

export interface ApiNotification {
  id: string
  user_id: string
  type: string
  title: string
  message: string
  read: boolean
  created_at: string
}

export async function getNotifications(userId: string): Promise<{ success: boolean; notifications: ApiNotification[]; unread_count: number }> {
  const res = await fetch(`${BASE_URL}/api/notifications/${userId}`)
  if (!res.ok) throw new Error(`Failed to get notifications: ${res.status}`)
  return res.json()
}

export async function markNotificationRead(notificationId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE_URL}/api/notifications/${notificationId}/read`, {
    method: 'PUT',
  })
  if (!res.ok) throw new Error(`Failed to mark notification read: ${res.status}`)
  return res.json()
}

export async function markAllNotificationsRead(userId: string): Promise<{ success: boolean; marked_read: number }> {
  const res = await fetch(`${BASE_URL}/api/notifications/${userId}/read-all`, {
    method: 'PUT',
  })
  if (!res.ok) throw new Error(`Failed to mark all read: ${res.status}`)
  return res.json()
}

export async function getUnreadCount(userId: string): Promise<{ unread_count: number }> {
  const res = await fetch(`${BASE_URL}/api/notifications/${userId}/unread-count`)
  if (!res.ok) return { unread_count: 0 }
  return res.json()
}

export function createInitialGraphNodes(): WorkflowGraphNode[] {
  return [
    { id: 'collect_profile_fn', label: 'Profile Agent', status: 'waiting' },
    { id: 'normalize_inventory_fn', label: 'Inventory Agent', status: 'waiting' },
    { id: 'search_recipe_fn', label: 'Recipe Agent', status: 'waiting' },
    { id: 'meal_plan_agent', label: 'Meal Plan Agent', status: 'waiting' },
    { id: 'shopping_agent', label: 'Shopping Agent', status: 'waiting' },
    { id: 'budget_feedback_fn', label: 'Budget Review', status: 'waiting' },
    { id: 'done_fn', label: 'Complete', status: 'waiting' },
  ]
}
