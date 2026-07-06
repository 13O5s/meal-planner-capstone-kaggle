import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, Sparkles, Loader2, Check, X, StopCircle, PanelRightClose, PanelRight } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { WorkflowGraph } from '@/components/workflow/WorkflowGraph'
import { useWorkflow } from '@/hooks/use-workflow'
import { useWorkflowStore } from '@/stores/workflow-store'
import { cn } from '@/lib/utils'
import type { AIMessage } from '@/types'

const suggestedPrompts = [
  'Generate a healthy 7-day meal plan for weight loss',
  'What can I cook with chicken and vegetables?',
  'Analyze my weekly nutrition',
  'Help me reduce my grocery budget',
  'Suggest high-protein breakfast ideas',
]

export function ChatPage() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<AIMessage[]>([])
  const [showGraph, setShowGraph] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { run, cancel, error } = useWorkflow()
  const graph = useWorkflowStore((s) => s.graph)
  const isRunning = useWorkflowStore((s) => s.isRunning)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const addMessage = useCallback((msg: AIMessage) => {
    setMessages((prev) => [...prev, msg])
  }, [])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || isRunning) return
    setInput('')

    const userMsg: AIMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMsg)

    await run(text)
  }, [input, isRunning, run, addMessage])

  const handleSuggestedPrompt = useCallback(
    async (prompt: string) => {
      const userMsg: AIMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: prompt,
        timestamp: new Date().toISOString(),
      }
      addMessage(userMsg)
      await run(prompt)
    },
    [run, addMessage]
  )

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const completedNodes = graph?.nodes.filter((n) => n.status === 'completed' || n.status === 'failed') ?? []

  return (
    <div className="flex h-[calc(100vh-4rem)] animate-fade-in">
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-6">
          {messages.length === 0 && !isRunning ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-16">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-5">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-xl font-semibold text-text mb-2">How can I help you today?</h2>
              <p className="text-sm text-text-secondary mb-8 max-w-md">
                Ask me to plan meals, analyze nutrition, find recipes, or optimize your shopping.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {suggestedPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSuggestedPrompt(prompt)}
                    className="px-4 py-2.5 rounded-xl border border-border text-sm text-text-secondary hover:bg-surface-variant hover:text-text transition-colors cursor-pointer"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    'flex gap-4',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-4 h-4 text-primary" />
                    </div>
                  )}

                  <div className={cn('max-w-2xl', msg.role === 'user' && 'order-first')}>
                    {msg.role === 'user' ? (
                      <div className="px-4 py-3 rounded-2xl bg-primary text-on-primary">
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    ) : (
                      <Card className="p-5">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap text-text">{msg.content}</p>
                        {msg.tool_calls && msg.tool_calls.length > 0 && (
                          <div className="mt-4 space-y-2">
                            <p className="text-xs text-text-muted font-medium uppercase tracking-wide">Tools used</p>
                            {msg.tool_calls.map((tool, i) => (
                              <div
                                key={i}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg bg-surface-variant text-sm"
                              >
                                {tool.status === 'completed' ? (
                                  <Check className="w-4 h-4 text-primary shrink-0" />
                                ) : tool.status === 'running' ? (
                                  <Loader2 className="w-4 h-4 text-blue animate-spin shrink-0" />
                                ) : (
                                  <X className="w-4 h-4 text-error shrink-0" />
                                )}
                                <span className="font-medium text-text">{tool.name}</span>
                                {tool.output && (
                                  <span className="text-text-muted ml-auto text-xs">
                                    {tool.output}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </Card>
                    )}
                  </div>

                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0 mt-1">
                      <User className="w-4 h-4 text-on-primary" />
                    </div>
                  )}
                </div>
              ))}

              {isRunning && (
                <div className="flex gap-4 justify-start">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4 text-primary" />
                  </div>
                  <Card className="p-5">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 text-primary animate-spin" />
                      <span className="text-sm text-text-secondary">Thinking...</span>
                    </div>
                    <div className="mt-3 space-y-1">
                      {completedNodes.map((n) => (
                        <div key={n.id} className="flex items-center gap-2 text-xs text-text-muted">
                          {n.status === 'completed' ? (
                            <Check className="w-3 h-3 text-primary" />
                          ) : n.status === 'failed' ? (
                            <X className="w-3 h-3 text-error" />
                          ) : null}
                          <span>{n.label}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              )}

              {error && (
                <div className="flex gap-4 justify-start">
                  <div className="w-8 h-8 rounded-full bg-error/10 flex items-center justify-center shrink-0 mt-1">
                    <X className="w-4 h-4 text-error" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl bg-error/10 border border-error/20 text-sm text-error">
                    {error}
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {isRunning && (
          <div className="px-4 lg:px-8 py-2">
            <Button variant="ghost" size="sm" onClick={cancel} className="text-error">
              <StopCircle className="w-4 h-4" />
              Stop generating
            </Button>
          </div>
        )}

        <div className="border-t border-border p-4 lg:p-6">
          <div className="flex items-end gap-3 max-w-3xl mx-auto">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                rows={1}
                disabled={isRunning}
                className="w-full px-4 py-3 rounded-xl border border-border bg-surface text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none transition-all disabled:opacity-50"
                onInput={(e) => {
                  const el = e.currentTarget
                  el.style.height = 'auto'
                  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
                }}
              />
            </div>
            <Button size="icon" disabled={!input.trim() || isRunning} onClick={handleSend}>
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      <div
        className={cn(
          'hidden lg:flex flex-col border-l border-border bg-surface transition-all duration-300 overflow-y-auto',
          showGraph ? 'w-80' : 'w-0 border-l-0 overflow-hidden'
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
          <h3 className="text-sm font-semibold text-text">Workflow</h3>
          <button
            onClick={() => setShowGraph(false)}
            className="p-1 rounded hover:bg-surface-variant transition-colors cursor-pointer"
            aria-label="Close workflow panel"
          >
            <PanelRightClose className="w-4 h-4 text-text-muted" />
          </button>
        </div>
        <div className="p-4">
          {graph ? (
            <WorkflowGraph />
          ) : (
            <p className="text-xs text-text-muted text-center py-8">
              No workflow running. Send a message to see the AI workflow in action.
            </p>
          )}
        </div>
      </div>

      {!showGraph && (
        <button
          onClick={() => setShowGraph(true)}
          className="hidden lg:flex fixed right-0 top-1/2 -translate-y-1/2 z-10 p-2 rounded-l-lg bg-surface border border-border border-r-0 hover:bg-surface-variant transition-colors cursor-pointer"
          aria-label="Show workflow panel"
        >
          <PanelRight className="w-4 h-4 text-text-muted" />
        </button>
      )}
    </div>
  )
}
