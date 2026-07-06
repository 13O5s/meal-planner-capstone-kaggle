# 🎨 Meal Planner UI

Frontend for Smart Meal Planner — React 19 + Vite 8 + Tailwind CSS 4.

---

## 🛠️ Tech Stack

| Technology | Version |
|------------|---------|
| React | 19.2 |
| TypeScript | 6.0 |
| Vite | 8.1 |
| Tailwind CSS | 4.3 |
| Zustand | 5.0 |
| Framer Motion | 12.42 |
| React Router DOM | 7.18 |
| Recharts | 3.9 |
| Lucide React | 1.23 |

---

## 📁 Project Structure

```
src/
├── pages/              11 pages
│   ├── DashboardPage
│   ├── ChatPage
│   ├── ProfilePage
│   ├── SetupProfilePage
│   ├── InventoryPage
│   ├── MealPlansPage
│   ├── ShoppingListsPage
│   ├── HistoryPage
│   ├── LoginPage
│   ├── RegisterPage
│   └── SettingsPage
├── components/
│   ├── ui/             Primitives: Button (5 variants), Card (3 variants)
│   ├── layout/         Sidebar, TopBar
│   ├── meal-plans/     MealCard, MealDayCard, MealStats, NutritionBadge
│   ├── shared/         EmptyState, Skeleton, WorkflowStepper
│   └── workflow/       WorkflowGraph
├── stores/
│   ├── auth-store      Authentication + localStorage persistence
│   ├── theme-store     Dark/light toggle + localStorage
│   ├── notification-store  WebSocket-connected notifications
│   └── workflow-store  Workflow graph state + step progression
├── lib/
│   ├── api.ts          All API calls (689 lines), SSE streaming
│   ├── styles.ts       Design token utility classes (card, typography, pill)
│   └── utils.ts        cn() Tailwind class merge
├── hooks/
│   └── use-workflow.ts
└── types/
    └── index.ts        All TypeScript interfaces (259 lines)
```

---

## 📋 Prerequisites

- Node.js 20+

---

## 🚀 Setup

```bash
# Install dependencies
npm install

# Set backend API URL (defaults to http://localhost:8000)
# Option A) .env file:
echo "VITE_API_URL=http://localhost:8000" > .env

# Option B) Inline (build-time):
VITE_API_URL=http://localhost:8000 npm run dev

# Start dev server
npm run dev
```

---

## 🧩 Component Patterns

### Button (`src/components/ui/button.tsx`)
- 5 variants: `primary`, `secondary`, `ghost`, `outline`, `danger`
- 4 sizes: `sm`, `md`, `lg`, `icon`
- Supports loading state (Lucide `Loader2` spinner)
- Uses `forwardRef`

### Card (`src/components/ui/card.tsx`)
- 3 variants: `default`, `elevated`, `interactive`
- Sub-components: `CardHeader`, `CardContent`
- Uses `forwardRef`

### Style Tokens (`src/lib/styles.ts`)
- `card` — `.wrapper`, `.header`, `.content`
- `typography` — `.h1`, `.subtitle`, `.sectionTitle`
- `button` — `.primary`, `.secondary`
- `pill` — `.base`, `.active`, `.inactive`
- `input` — `.base`, `.date`

---

## 🗺️ Routing

| Route | Access |
|-------|--------|
| `/login`, `/register` | Unauthenticated only |
| `/setup-profile` | Authenticated, profile incomplete |
| `/dashboard`, `/profile`, `/inventory` | Authenticated + profile complete |
| `/meal-plans`, `/shopping-lists`, `/history`, `/settings` | Authenticated + profile complete |

Protected by conditional routing in `App.tsx` using `ProtectedLayout` (collapsible Sidebar + TopBar).

---

## 🌐 API Layer

- Base URL from `VITE_API_URL` env var (default: `http://localhost:8000`)
- SSE streaming via `runAgentSSE` for real-time agent progress
- All endpoints centralized in `src/lib/api.ts`
- LocalStorage for session ID + inventory cache

---

## 🎨 Styling

- **Tailwind CSS 4** with custom theme in `src/index.css`
- Dark/light mode via `.dark` class toggle
- Custom animations: `animate-fade-in`, `animate-slide-up`, `animate-shimmer`, `animate-pulse-glow`
- Icons: Lucide React (consistent `w-4 h-4` / `w-5 h-5`)
- Micro-interactions: Framer Motion (staggered lists, `AnimatePresence`, layout animations)

---

## 🏗️ Build & Deploy

```bash
npm run build       # TypeScript check + Vite build → dist/
npm run preview     # Serve built dist locally
```

### Docker

```bash
docker build --build-arg VITE_API_URL=https://your-api-url ... -t meal-plan-ui .
```

### Cloud Build

Trigger with substitution `_VITE_API_URL` set to backend URL. See `cloudbuild.yaml`.

---

## 🔗 Related

- **Backend README** (`../meal-planner-assistant/README.md`)
- **Root README** (`../README.md`)
