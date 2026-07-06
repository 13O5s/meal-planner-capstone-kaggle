import { useState, useCallback, useRef } from 'react'
import { useWorkflowStore } from '@/stores/workflow-store'
import { checkAiQuota, createSession, runAgentSSE } from '@/lib/api'
import type { SSEStatus } from '@/types'

export function useWorkflow() {
  const store = useWorkflowStore()
  const [status, setStatus] = useState<SSEStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const run = useCallback(
    async (text: string, userId = 'test_user') => {
      setStatus('connecting')
      setError(null)

      try {
        const quota = await checkAiQuota()
        if (!quota.available) {
          setError(quota.error || 'Daily AI quota exceeded. Please try again later or upgrade your plan.')
          setStatus('error')
          return
        }

        const session = await createSession(userId)

        const { getUserProfile, updateSessionState } = await import('@/lib/api')
        try {
          const raw = localStorage.getItem('meal_planner_inventory')
          const inventory: Record<string, unknown>[] = raw ? JSON.parse(raw) : []
          const profile = await getUserProfile(userId)
          const delta: Record<string, unknown> = {}
          if (profile) delta.user_profile = profile
          if (inventory.length > 0) delta.available_ingredients = inventory
          if (Object.keys(delta).length > 0) {
            await updateSessionState(session.id, delta, userId)
          }
        } catch { /* non-blocking pre-populate */ }

        store.startRun(session.id)

        setStatus('streaming')

        await runAgentSSE(text, userId, session.id, {
          onNodeProgress: (nodeId, status, detail) => {
            store.updateNodeStatus(nodeId, status, detail)
          },
          onComplete: () => {
            store.completeRun()
            setStatus('completed')
          },
          onError: (err) => {
            store.failRun('done_fn')
            setError(err.message)
            setStatus('error')
          },
        })
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        setError(msg)
        setStatus('error')
      }
    },
    [store]
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    store.reset()
    setStatus('idle')
  }, [store])

  const selectNode = useCallback(
    (nodeId: string | null) => {
      store.selectNode(nodeId)
    },
    [store]
  )

  return {
    status,
    error,
    graph: store.graph,
    selectedNodeId: store.selectedNodeId,
    steps: store.steps,
    isRunning: store.isRunning,
    run,
    cancel,
    selectNode,
  }
}
