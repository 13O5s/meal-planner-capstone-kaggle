import { useWorkflowStore } from '@/stores/workflow-store'
import type { WorkflowGraphNode, NodeDetail } from '@/types'
import { Check, Loader2, X, ChevronDown, ChevronRight, Clock, Wrench, Database, Eye } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

const statusStyles: Record<string, string> = {
  completed:
    'border-primary dark:border-primary-dark bg-primary/5 dark:bg-primary-dark/5',
  running:
    'border-tertiary dark:border-tertiary-dark bg-tertiary/5 dark:bg-tertiary-dark/5 ring-2 ring-tertiary/30 dark:ring-tertiary-dark/30',
  failed:
    'border-error dark:border-error-dark bg-error/5 dark:bg-error-dark/5',
  waiting:
    'border-outline-variant dark:border-outline-variant-dark bg-surface dark:bg-surface-dark opacity-50',
}

const statusIcon = (status: WorkflowGraphNode['status']) => {
  switch (status) {
    case 'completed':
      return <Check className="w-4 h-4 text-primary dark:text-primary-dark" />
    case 'running':
      return <Loader2 className="w-4 h-4 text-tertiary dark:text-tertiary-dark animate-spin" />
    case 'failed':
      return <X className="w-4 h-4 text-error dark:text-error-dark" />
    default:
      return <div className="w-2 h-2 rounded-full bg-outline-variant dark:bg-outline-variant-dark" />
  }
}

const statusIconBg: Record<string, string> = {
  completed: 'bg-primary/10 dark:bg-primary-dark/10',
  running: 'bg-tertiary/10 dark:bg-tertiary-dark/10',
  failed: 'bg-error/10 dark:bg-error-dark/10',
  waiting: 'bg-surface-variant dark:bg-surface-variant-dark',
}

function NodeDetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 py-1.5">
      <span className="text-xs text-outline dark:text-outline-dark font-medium min-w-[80px] shrink-0">{label}</span>
      <div className="text-xs text-[#1C1B1F] dark:text-[#E6E1E5]">{children}</div>
    </div>
  )
}

function NodeDetailCard({ detail }: { detail: NodeDetail; nodeId: string }) {
  if (!detail) return null

  return (
    <div className="mt-3 pt-3 border-t border-outline-variant dark:border-outline-variant-dark space-y-2">
      {detail.executionTime && (
        <div className="flex items-center gap-1.5 text-xs text-outline dark:text-outline-dark">
          <Clock className="w-3 h-3" />
          {detail.executionTime}
        </div>
      )}

      {detail.inputSummary && (
        <NodeDetailRow label="Input">
          <span className="text-outline dark:text-outline-dark">{detail.inputSummary}</span>
        </NodeDetailRow>
      )}

      {detail.outputSummary && (
        <NodeDetailRow label="Output">
          <span className="text-outline dark:text-outline-dark">{detail.outputSummary}</span>
        </NodeDetailRow>
      )}

      {detail.toolsUsed.length > 0 && (
        <NodeDetailRow label="Tools">
          <div className="space-y-1">
            {detail.toolsUsed.map((tool, i) => (
              <div key={i} className="flex items-center gap-2">
                <Wrench className="w-3 h-3 text-outline dark:text-outline-dark shrink-0" />
                <span className="font-medium">{tool.name}</span>
                {tool.status === 'completed' && (
                  <Check className="w-3 h-3 text-primary dark:text-primary-dark" />
                )}
                {tool.status === 'failed' && <X className="w-3 h-3 text-error dark:text-error-dark" />}
                {tool.duration && (
                  <span className="text-outline dark:text-outline-dark">({tool.duration})</span>
                )}
              </div>
            ))}
          </div>
        </NodeDetailRow>
      )}

      {detail.mcpServices.length > 0 && (
        <NodeDetailRow label="MCP">
          <div className="space-y-1">
            {detail.mcpServices.map((svc, i) => (
              <div key={i} className="flex items-center gap-2">
                <Database className="w-3 h-3 text-outline dark:text-outline-dark shrink-0" />
                <span>{svc.server}/{svc.tool}</span>
                {svc.status === 'completed' && (
                  <Check className="w-3 h-3 text-primary dark:text-primary-dark" />
                )}
              </div>
            ))}
          </div>
        </NodeDetailRow>
      )}

      {detail.validationResults && detail.validationResults.length > 0 && (
        <NodeDetailRow label="Validations">
          <ul className="list-disc list-inside space-y-0.5">
            {detail.validationResults.map((r, i) => (
              <li key={i} className="text-outline dark:text-outline-dark">{r}</li>
            ))}
          </ul>
        </NodeDetailRow>
      )}
    </div>
  )
}

function GraphNode({
  node,
  isLast,
  selected,
  onSelect,
}: {
  node: WorkflowGraphNode
  index: number
  isLast: boolean
  selected: boolean
  onSelect: (id: string | null) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const hasDetail = node.detail && (node.detail.toolsUsed.length > 0 || node.detail.executionTime || node.detail.inputSummary)

  return (
    <div className="relative">
      {/* Vertical connector line */}
      {!isLast && (
        <div className="absolute left-[19px] top-10 bottom-0 w-0.5 bg-outline-variant dark:bg-outline-variant-dark" />
      )}

      <div
        className={cn(
          'relative flex gap-3 p-4 rounded-xl border transition-all duration-300 cursor-pointer hover:shadow-sm',
          statusStyles[node.status],
          selected && 'ring-2 ring-primary dark:ring-primary-dark'
        )}
        onClick={() => onSelect(selected ? null : node.id)}
      >
        {/* Status icon */}
        <div
          className={cn(
            'w-10 h-10 rounded-xl flex items-center justify-center shrink-0 mt-0.5',
            statusIconBg[node.status]
          )}
        >
          {statusIcon(node.status)}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold">{node.label}</h3>
            <div className="flex items-center gap-1">
              {node.status === 'running' && (
                <span className="text-xs text-tertiary dark:text-tertiary-dark font-medium animate-pulse">
                  Running...
                </span>
              )}
              {hasDetail && (
                <button
                  onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
                  className="p-0.5 rounded hover:bg-surface-variant dark:hover:bg-surface-variant-dark transition-colors cursor-pointer"
                  aria-label={expanded ? 'Collapse details' : 'Expand details'}
                >
                  {expanded ? (
                    <ChevronDown className="w-4 h-4 text-outline dark:text-outline-dark" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-outline dark:text-outline-dark" />
                  )}
                </button>
              )}
            </div>
          </div>

          <p className="text-xs text-outline dark:text-outline-dark mt-0.5">
            {node.id === 'collect_profile_fn' && 'Collect user health profile'}
            {node.id === 'normalize_inventory_fn' && 'Parse and normalize ingredients'}
            {node.id === 'search_recipe_fn' && 'Find matching recipes'}
            {node.id === 'meal_plan_agent' && 'Generate meal plan with nutrition'}
            {node.id === 'shopping_agent' && 'Optimize shopping list'}
            {node.id === 'budget_feedback_fn' && 'Check budget and get feedback'}
            {node.id === 'done_fn' && 'Final summary'}
          </p>

          {expanded && node.detail && (
            <NodeDetailCard detail={node.detail} nodeId={node.id} />
          )}

          {selected && node.status === 'completed' && node.detail && !expanded && (
            <button
              onClick={(e) => { e.stopPropagation(); setExpanded(true) }}
              className="flex items-center gap-1 mt-2 text-xs text-primary dark:text-primary-dark font-medium hover:underline cursor-pointer"
            >
              <Eye className="w-3 h-3" />
              Inspect details
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export function WorkflowGraph() {
  const graph = useWorkflowStore((s) => s.graph)
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId)
  const selectNode = useWorkflowStore((s) => s.selectNode)

  if (!graph) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Workflow Progress</h3>
        {graph.startedAt && (
          <span className="text-xs text-outline dark:text-outline-dark">
            Started {new Date(graph.startedAt).toLocaleTimeString()}
          </span>
        )}
      </div>

      <div className="space-y-0">
        {graph.nodes.map((node, index) => (
          <GraphNode
            key={node.id}
            node={node}
            index={index}
            isLast={index === graph.nodes.length - 1}
            selected={selectedNodeId === node.id}
            onSelect={selectNode}
          />
        ))}
      </div>

      {graph.completedAt && (
        <p className="text-xs text-outline dark:text-outline-dark text-center pt-2">
          Completed at {new Date(graph.completedAt).toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}
