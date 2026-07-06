export interface UserProfile {
  age: number | null
  gender: string | null
  height_cm: number | null
  weight_kg: number | null
  target_weight_kg: number | null
  activity_level: string
  daily_calorie_target: number | null
  daily_protein_target: number | null
  daily_carbs_target: number | null
  daily_fat_target: number | null
  favorite_foods: string[]
  disliked_foods: string[]
  allergies: string[]
  dietary_preferences: string[]
  budget: number | null
  meals_per_day: number
  goal: string
  cooking_skill_level?: string
  preferred_cuisines?: string[]
}

export interface Ingredient {
  id: string
  name: string
  quantity: number
  unit: string
  category: string
  expiry?: string
  available?: boolean
}

export interface Recipe {
  id: string
  title: string
  image?: string
  cooking_time: number
  calories: number
  protein: number
  carbs: number
  fat: number
  difficulty: 'easy' | 'medium' | 'hard'
  estimated_cost: number
  cuisine?: string
  ingredients: RecipeIngredient[]
  instructions: string[]
  tags: string[]
}

export interface RecipeIngredient {
  name: string
  quantity: number
  unit: string
  available?: boolean
}

export interface MealSlot {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  recipe: Recipe
  prep_notes?: string
}

export interface MealDay {
  day: string
  meals: MealSlot[]
  total_nutrition: {
    calories: number
    protein: number
    carbs: number
    fat: number
  }
}

export interface MealPlan {
  id: string
  strategy: string
  days: number
  meals_per_day: number
  schedule: MealDay[]
  estimated_cost: number
  budget: number
  created_at: string
}

export interface ShoppingItem {
  id: string
  name: string
  quantity: number
  unit: string
  category: string
  estimated_price: number
  purchased: boolean
  store?: string
  alternative?: string
  notes?: string
}

export interface ShoppingList {
  id: string
  meal_plan_id: string
  items: ShoppingItem[]
  total_cost: number
  budget: number
  money_saved: number
  waste_reduced: number
  created_at: string
}

export interface HistoryEntry {
  id: string
  type: 'meal_plan' | 'recipe' | 'shopping_list' | 'profile_update'
  title: string
  created_at: string
  data: Record<string, unknown>
}

export type WorkflowNodeStatus = 'waiting' | 'running' | 'completed' | 'failed'

export interface ToolInvocation {
  name: string
  status: 'running' | 'completed' | 'failed'
  input?: string
  output?: string
  duration?: string
}

export interface MCPInvocation {
  server: string
  tool: string
  status: 'running' | 'completed' | 'failed'
  duration?: string
}

export interface NodeDetail {
  inputSummary: string
  outputSummary: string
  executionTime: string
  toolsUsed: ToolInvocation[]
  mcpServices: MCPInvocation[]
  validationResults?: string[]
}

export interface WorkflowGraphNode {
  id: string
  label: string
  status: WorkflowNodeStatus
  detail?: NodeDetail
}

export interface WorkflowGraph {
  id: string
  nodes: WorkflowGraphNode[]
  startedAt?: string
  completedAt?: string
}

export type WorkflowStepStatus = 'pending' | 'active' | 'completed' | 'error'

export interface WorkflowStep {
  id: string
  label: string
  status: WorkflowStepStatus
  duration?: string
}

export interface WorkflowState {
  isRunning: boolean
  steps: WorkflowStep[]
  currentStep: number
  graph: WorkflowGraph | null
}

export interface AIMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  tool_calls?: ToolInvocation[]
  workflowGraph?: WorkflowGraph
  timestamp: string
}

export interface ToolCall {
  name: string
  status: 'running' | 'completed' | 'failed'
  input?: string
  output?: string
}

export interface NutritionSummary {
  calories: number
  protein: number
  carbs: number
  fat: number
  calorie_target: number
  protein_target: number
  carbs_target: number
  fat_target: number
}

/* ─── ADK / API Types ─── */

export interface ADKEvent {
  id: string
  author: string
  invocation_id: string
  content?: {
    parts?: ADKPart[]
    role?: string
  }
  actions?: {
    state_delta?: Record<string, unknown>
    skip_summarization?: boolean
    interrupt?: unknown
  }
  timestamp?: string
  finished?: boolean
  error?: string
}

export interface ADKPart {
  text?: string
  function_call?: {
    name: string
    args?: Record<string, unknown>
    id?: string
  }
  function_response?: {
    name: string
    response?: Record<string, unknown>
    id?: string
  }
  tool_request?: {
    name: string
    input?: string
  }
  tool_response?: {
    name: string
    output?: string
    status?: string
  }
}

export interface SessionInfo {
  id: string
  app_name: string
  user_id: string
  state?: Record<string, unknown>
}

export interface RunRequest {
  new_message: {
    role: string
    parts: Array<{ text: string } | { function_call?: unknown } | { function_response?: unknown }>
  }
  user_id: string
  session_id: string
}

export type SSEStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'error'
