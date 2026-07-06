import { create } from 'zustand'
import type { WorkflowGraph, WorkflowGraphNode, NodeDetail, WorkflowStep, ToolInvocation } from '@/types'
import { WORKFLOW_NODE_ORDER, getNodeLabel, createInitialGraphNodes, setLastSessionId } from '@/lib/api'

interface WorkflowState {
  isRunning: boolean
  steps: WorkflowStep[]
  currentStep: number
  graph: WorkflowGraph | null
  selectedNodeId: string | null
  sessionId: string | null
  lastSessionId: string | null
}

interface WorkflowActions {
  startRun: (sessionId: string) => void
  updateNodeStatus: (nodeId: string, status: WorkflowGraphNode['status'], detail?: NodeDetail) => void
  setNodeDetail: (nodeId: string, detail: NodeDetail) => void
  selectNode: (nodeId: string | null) => void
  addToolToNode: (nodeId: string, tool: ToolInvocation) => void
  completeRun: () => void
  failRun: (nodeId: string, error?: string) => void
  reset: () => void
}

const initialState: WorkflowState = {
  isRunning: false,
  steps: [],
  currentStep: -1,
  graph: null,
  selectedNodeId: null,
  sessionId: null,
  lastSessionId: null,
}

export const useWorkflowStore = create<WorkflowState & WorkflowActions>((set) => ({
  ...initialState,

  startRun: (sessionId) =>
    set((state) => ({
      isRunning: true,
      sessionId,
      currentStep: 0,
      graph: {
        id: crypto.randomUUID(),
        nodes: createInitialGraphNodes(),
        startedAt: new Date().toISOString(),
      },
      steps: WORKFLOW_NODE_ORDER.map((id, i) => ({
        id,
        label: getNodeLabel(id),
        status: i === 0 ? 'active' : 'pending',
      })),
      lastSessionId: state.lastSessionId,
    })),

  updateNodeStatus: (nodeId, status, detail) =>
    set((state) => {
      if (!state.graph) return state

      const nodeIndex = WORKFLOW_NODE_ORDER.indexOf(nodeId)
      const nextStep = status === 'completed' ? Math.min(nodeIndex + 1, WORKFLOW_NODE_ORDER.length - 1) : nodeIndex

      return {
        graph: {
          ...state.graph,
          nodes: state.graph.nodes.map((n) =>
            n.id === nodeId
              ? { ...n, status, detail: detail ? { ...n.detail, ...detail } : n.detail }
              : n
          ),
        },
        currentStep: nextStep >= 0 ? nextStep : state.currentStep,
        steps: state.steps.map((s, i) => {
          if (s.id === nodeId) {
            const mapStatus: Record<string, WorkflowStep['status']> = {
              waiting: 'pending',
              running: 'active',
              completed: 'completed',
              failed: 'error',
            }
            return { ...s, status: mapStatus[status] || s.status }
          }
          if (i === nextStep && status === 'completed') {
            return { ...s, status: 'active' }
          }
          return s
        }),
      }
    }),

  setNodeDetail: (nodeId, detail) =>
    set((state) => ({
      graph: state.graph
        ? {
            ...state.graph,
            nodes: state.graph.nodes.map((n) =>
              n.id === nodeId ? { ...n, detail: { ...n.detail, ...detail } } : n
            ),
          }
        : null,
    })),

  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

  addToolToNode: (nodeId, tool) =>
    set((state) => ({
      graph: state.graph
        ? {
            ...state.graph,
            nodes: state.graph.nodes.map((n) =>
              n.id === nodeId
                ? {
                    ...n,
                    detail: {
                      ...n.detail!,
                      toolsUsed: [...(n.detail?.toolsUsed ?? []), tool],
                    },
                  }
                : n
            ),
          }
        : null,
    })),

  completeRun: () =>
    set((state) => {
      const lastSid = state.sessionId
      if (lastSid) setLastSessionId(lastSid)
      return {
        isRunning: false,
        lastSessionId: lastSid || state.lastSessionId,
        graph: state.graph
          ? { ...state.graph, completedAt: new Date().toISOString() }
          : null,
      }
    }),

  failRun: (nodeId, _error) =>
    set((state) => ({
      isRunning: false,
      graph: state.graph
        ? {
            ...state.graph,
            nodes: state.graph.nodes.map((n) =>
              n.id === nodeId ? { ...n, status: 'failed' } : n
            ),
          }
        : null,
      steps: state.steps.map((s) =>
        s.id === nodeId ? { ...s, status: 'error' as const } : s
      ),
    })),

  reset: () => set(initialState),
}))
