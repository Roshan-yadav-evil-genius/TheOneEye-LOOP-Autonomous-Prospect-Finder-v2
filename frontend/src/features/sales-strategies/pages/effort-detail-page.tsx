import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

import { apiClient } from '../../../shared/api/client'
import { Button } from '../../../shared/components/button'
import { SplitFormChatLayout } from '../../../shared/components/split-form-chat-layout'
import { useWorkspaceContextStore } from '../stores/workspace-context-store'
import {
  getCompanyFinderEfforts,
  getContactFinderEfforts,
  getEffortDetail,
  type AgentRunSummary,
  type EffortDetailRead,
} from '../api/efforts-api'
import { trimThreadId, formatThreadRoleLabel } from '../utils/thread-utils'
import type { ChatHistoryRead } from '../../setup-chat/api/setup-chat-api-client'
import { ChatMessageList } from '../../setup-chat/components/chat-message-list'
import type { ChatUiMessage } from '../../setup-chat/stores/store-factory'
import { SetupChatPanel } from '../../setup-chat/components/SetupChatPanel'
import { useEffortChatStore } from '../stores/effort-chat-store'

export function EffortDetailPage({ role }: { role: 'company-finder' | 'contact-finder' }) {
  const { orgId = '', strategyId = '', companyId, effortSeq = '' } = useParams()
  const navigate = useNavigate()

  const { bundle, load: loadContext } = useWorkspaceContextStore()
  const chatStore = useEffortChatStore()

  const [effort, setEffort] = useState<EffortDetailRead | null>(null)
  const [loadingEffort, setLoadingEffort] = useState(true)
  const [effortError, setEffortError] = useState<string | null>(null)

  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatUiMessage[]>([])
  const [loadingChat, setLoadingChat] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const plannerThreadId = effort?.effort_prefix
    ? `${effort.effort_prefix}_planner`
    : ''

  // 0. Load Strategy Context & Effort Chat History for Planner Thread
  useEffect(() => {
    if (strategyId) {
      void loadContext(strategyId)
    }
  }, [loadContext, strategyId])

  useEffect(() => {
    if (effort?.effort_prefix && plannerThreadId) {
      useEffortChatStore.setState({ activeThreadId: plannerThreadId })
      void chatStore.loadHistory(effort.effort_prefix, plannerThreadId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effort?.effort_prefix, plannerThreadId])

  // 1. Fetch Effort Detail
  useEffect(() => {
    let mounted = true
    if (!strategyId || !effortSeq) return

    setLoadingEffort(true)
    setEffortError(null)

    const fetchEffort = async () => {
      try {
        let summaries: AgentRunSummary[] = []
        if (role === 'company-finder') {
          summaries = await getCompanyFinderEfforts(strategyId)
        } else {
          summaries = await getContactFinderEfforts(strategyId, companyId)
        }

        const seqNum = Number(effortSeq)
        let matched = summaries.find(
          (s) =>
            s.attempt_iteration === seqNum ||
            s.contact_attempt_iteration === seqNum ||
            s.effort_prefix.endsWith(`_${effortSeq}`)
        )

        let effortDetail: EffortDetailRead | null = null
        if (matched) {
          effortDetail = await getEffortDetail(matched.effort_prefix)
        } else {
          // Attempt direct lookup by effort prefix format fallback
          const reconstructedPrefix = `LOOP_${orgId}_${strategyId}_${effortSeq}`
          try {
            effortDetail = await getEffortDetail(reconstructedPrefix)
          } catch {
            if (summaries.length > 0) {
              effortDetail = await getEffortDetail(summaries[0].effort_prefix)
            }
          }
        }

        if (!mounted) return
        if (effortDetail) {
          setEffort(effortDetail)
          const pThreadId = `${effortDetail.effort_prefix}_planner`
          useEffortChatStore.setState({ activeThreadId: pThreadId })
          void chatStore.loadHistory(effortDetail.effort_prefix, pThreadId)

          // Default to primary thread if not selected
          const threads = Array.from(
            new Set([effortDetail.primary_thread_id, ...(effortDetail.child_thread_ids || [])])
          )
          if (threads.length > 0) {
            setSelectedThreadId(threads[0])
          }
        } else {
          setEffortError(`Effort #${effortSeq} not found`)
        }
      } catch (err: any) {
        if (!mounted) return
        setEffortError(err.message || 'Failed to load effort details')
      } finally {
        if (mounted) setLoadingEffort(false)
      }
    }

    void fetchEffort()
    return () => {
      mounted = false
    }
  }, [strategyId, companyId, effortSeq, role, orgId])

  // 2. Fetch Chat History when selectedThreadId changes
  useEffect(() => {
    let mounted = true
    if (!selectedThreadId) {
      setMessages([])
      return
    }

    setLoadingChat(true)
    setChatError(null)

    apiClient
      .get<ChatHistoryRead>(`/api/v1/threads/${encodeURIComponent(selectedThreadId)}/chat/history`)
      .then((res) => {
        if (!mounted) return

        const uiMessages: ChatUiMessage[] = []
        res.data.messages.forEach((msgDict: any, i: number) => {
          const type = msgDict.type
          const data = msgDict.data || {}

          if (type === 'human') {
            const content =
              typeof data.content === 'string' ? data.content : JSON.stringify(data.content)
            const lastMsg = uiMessages[uiMessages.length - 1]
            if (lastMsg && lastMsg.kind === 'user' && lastMsg.content === content) {
              return
            }
            uiMessages.push({ id: `hist-${i}`, kind: 'user', content })
          } else if (type === 'ai') {
            const aiMessageId = msgDict.id || data.id || `hist-${i}`
            const meta: any = { raw: msgDict }
            if (data.usage_metadata) meta.usage_metadata = data.usage_metadata
            if (data.response_metadata) meta.response_metadata = data.response_metadata
            if (aiMessageId) meta.id = aiMessageId

            let reasoning =
              data.additional_kwargs?.reasoning_content || data.additional_kwargs?.reasoning
            if (!reasoning && Array.isArray(data.content)) {
              const rBlock = data.content.find((b: any) => b.type === 'reasoning')
              if (rBlock) reasoning = rBlock.text
            }

            const toolCalls = data.tool_calls || []
            const contentStr =
              typeof data.content === 'string' ? data.content : JSON.stringify(data.content)

            const metadataObj = Object.keys(meta).length > 0 ? meta : undefined

            if (reasoning) {
              uiMessages.push({
                id: `hist-${i}-rsn`,
                aiMessageId,
                kind: 'reasoning',
                text: reasoning,
                metadata: metadataObj,
              })
            }

            if (contentStr && contentStr !== '""' && contentStr !== '[]' && contentStr !== '"[]"') {
              uiMessages.push({
                id: `hist-${i}-ast`,
                aiMessageId,
                kind: 'assistant',
                content: contentStr,
                metadata: metadataObj,
              })
            }

            toolCalls.forEach((tc: any, tcIdx: number) => {
              uiMessages.push({
                id: `hist-${i}-tc-${tcIdx}`,
                aiMessageId,
                kind: 'tool_call',
                name: tc.name,
                args: tc.args,
                metadata: metadataObj,
              })
            })

            if (
              !reasoning &&
              (!contentStr || contentStr === '""' || contentStr === '[]' || contentStr === '"[]"') &&
              toolCalls.length === 0
            ) {
              uiMessages.push({
                id: `hist-${i}-ast`,
                aiMessageId,
                kind: 'assistant',
                content: '',
                metadata: metadataObj,
              })
            }
          } else if (type === 'tool') {
            uiMessages.push({
              id: `hist-${i}-tr`,
              kind: 'tool_result',
              name: data.name,
              content:
                typeof data.content === 'string' ? data.content : JSON.stringify(data.content),
            })
          }
        })

        setMessages(uiMessages)
        setLoadingChat(false)
      })
      .catch((err) => {
        if (!mounted) return
        setChatError(err.message || 'Failed to load thread history')
        setLoadingChat(false)
      })

    return () => {
      mounted = false
    }
  }, [selectedThreadId])

  // Gather thread list
  const threads = useMemo(() => {
    if (!effort) return []
    const list = [effort.primary_thread_id, ...(effort.child_thread_ids || [])]
    return Array.from(new Set(list))
  }, [effort])

  const org = bundle?.organization
  const product = bundle?.product
  const strategy = bundle?.sales_strategy
  const currentRoleName = role === 'company-finder' ? 'Company finder' : 'Contact finder'
  const parentPath = companyId
    ? `/orgs/${orgId}/sales-strategies/${strategyId}/companies/${companyId}/contact-finder`
    : `/orgs/${orgId}/sales-strategies/${strategyId}/${role}`

  const breadcrumbs = [
    { label: 'Organizations', to: '/orgs' },
    ...(org
      ? [{
        label: org.name,
        to: `/orgs/${org.id}`,
        thumbnailUrl: (org as any).thumbnail_url,
        fallbackThumbnailUrl: '/static/org_placeholder.png',
      }]
      : [{ label: 'Organization', to: `/orgs/${orgId}` }]),
    ...(org && product
      ? [{
        label: product.name,
        to: `/orgs/${org.id}/products/${product.id}`,
        thumbnailUrl: (product as any).thumbnail_url,
        fallbackThumbnailUrl: '/static/product_service_placeholder.png',
      }]
      : []),
    ...(strategy
      ? [{
        label: strategy.name,
        to: parentPath,
        thumbnailUrl: (strategy as any).thumbnail_url,
        fallbackThumbnailUrl: '/static/strategy_placeholder.png',
      }]
      : []),
    { label: currentRoleName, to: parentPath },
    { label: `Effort #${effortSeq}` },
  ]

  const handleCopyThreadId = () => {
    if (selectedThreadId && navigator.clipboard) {
      void navigator.clipboard.writeText(selectedThreadId)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (loadingEffort) {
    return (
      <div className="split-layout-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <p className="muted">Loading Effort #{effortSeq} details...</p>
      </div>
    )
  }

  if (effortError || !effort) {
    return (
      <div className="split-layout-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <p style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--color-danger)' }}>
          {effortError || 'Effort not found'}
        </p>
        <Button variant="outline" style={{ marginTop: '1rem' }} onClick={() => navigate(parentPath)}>
          Return to {currentRoleName}
        </Button>
      </div>
    )
  }

  return (
    <SplitFormChatLayout
      title={`${currentRoleName} · Effort #${effortSeq}`}
      subtitle={`Iteration #${effort.attempt_iteration ?? effortSeq} · ${threads.length} ${threads.length === 1 ? 'thread' : 'threads'} · Status: ${effort.status.toUpperCase()}`}
      breadcrumbs={breadcrumbs}
      actions={
        <>
          {selectedThreadId && (
            <Button variant="outline" onClick={handleCopyThreadId}>
              {copied ? '✓ Copied' : '📋 Copy Thread ID'}
            </Button>
          )}
          <Button variant="ghost" onClick={() => navigate(parentPath)}>
            ← {currentRoleName}
          </Button>
        </>
      }
      leftPanelStyle={{ flex: '1 1 58%', padding: 0, overflow: 'hidden' }}
      rightPanelStyle={{ flex: '1 1 42%', padding: '1.25rem', overflow: 'hidden' }}
      leftPanel={
        <div style={{ display: 'flex', flexDirection: 'row', height: '100%', width: '100%', overflow: 'hidden' }}>
          {/* Thread List Sidebar */}
          <div
            style={{
              flex: '0 0 240px',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              overflow: 'hidden',
              borderRight: '1px solid var(--color-border-default)',
            }}
          >
            {/* Sidebar Header */}
            <div
              style={{
                padding: '14px 16px',
                borderBottom: '1px solid var(--color-border-default)',
                background: 'rgba(255, 255, 255, 0.02)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexShrink: 0,
              }}
            >
              <span style={{ fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.04em', color: 'var(--color-text-secondary)' }}>
                EFFORT THREADS
              </span>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '2px 7px',
                  borderRadius: '12px',
                  background:
                    effort.status === 'completed'
                      ? 'rgba(34, 197, 94, 0.15)'
                      : effort.status === 'running'
                      ? 'rgba(59, 130, 246, 0.15)'
                      : 'rgba(239, 68, 68, 0.15)',
                  color:
                    effort.status === 'completed'
                      ? '#4ade80'
                      : effort.status === 'running'
                      ? '#60a5fa'
                      : '#f87171',
                  border: `1px solid ${
                    effort.status === 'completed'
                      ? 'rgba(34, 197, 94, 0.3)'
                      : effort.status === 'running'
                      ? 'rgba(59, 130, 246, 0.3)'
                      : 'rgba(239, 68, 68, 0.3)'
                  }`,
                  textTransform: 'uppercase',
                }}
              >
                {effort.status}
              </span>
            </div>

            {/* Thread Nav List */}
            <nav style={{ flex: 1, overflowY: 'auto', padding: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {threads.map((threadId) => {
                const trimmed = trimThreadId(threadId, effort.effort_prefix)
                const meta = formatThreadRoleLabel(trimmed, effort.agent_role)
                const isSelected = threadId === selectedThreadId

                return (
                  <button
                    key={threadId}
                    type="button"
                    onClick={() => setSelectedThreadId(threadId)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      border: isSelected
                        ? '1px solid var(--color-accent-primary, #3b82f6)'
                        : '1px solid transparent',
                      background: isSelected
                        ? 'rgba(59, 130, 246, 0.12)'
                        : 'transparent',
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    <span style={{ fontSize: '1.2rem', lineHeight: 1, flexShrink: 0 }}>{meta.icon}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontWeight: isSelected ? 700 : 600,
                          fontSize: '0.85rem',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          color: isSelected ? '#ffffff' : 'var(--color-text-primary)',
                        }}
                      >
                        {meta.title}
                      </div>
                      <div
                        style={{
                          fontSize: '0.74rem',
                          color: 'var(--color-text-secondary)',
                          marginTop: '2px',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {meta.subtitle}
                      </div>
                    </div>
                    {threadId === effort.primary_thread_id && (
                      <span
                        style={{
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          padding: '2px 5px',
                          borderRadius: '4px',
                          background: 'rgba(59, 130, 246, 0.2)',
                          color: '#93c5fd',
                          flexShrink: 0,
                        }}
                      >
                        MAIN
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Selected Thread Execution Log & Reasoning Viewer */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', minWidth: 0 }}>
            {/* Thread Header */}
            <div
              style={{
                padding: '12px 16px',
                borderBottom: '1px solid var(--color-border-default)',
                background: 'rgba(255, 255, 255, 0.02)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexShrink: 0,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                <span style={{ fontWeight: 700, fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {selectedThreadId
                    ? trimThreadId(selectedThreadId, effort.effort_prefix)
                    : 'Select a thread'}
                </span>
                {selectedThreadId && (
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontFamily: 'monospace',
                      color: 'var(--color-text-secondary)',
                      background: 'rgba(255,255,255,0.05)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {selectedThreadId}
                  </span>
                )}
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', flexShrink: 0 }}>
                Execution Log & Agent Reasoning
              </span>
            </div>

            {/* Execution Log / Reasoning Transcript */}
            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: '12px 16px', minHeight: 0 }}>
              {loadingChat ? (
                <p className="muted" style={{ margin: 'auto' }}>
                  Loading thread transcript...
                </p>
              ) : chatError ? (
                <p style={{ color: 'var(--color-danger)', margin: 'auto' }}>{chatError}</p>
              ) : (
                <ChatMessageList messages={messages} emptyMessage="No execution history found for this thread." />
              )}
            </div>
          </div>
        </div>
      }
      rightPanel={
        <SetupChatPanel
          title={role === 'company-finder' ? 'Company Finder Planner Agent' : 'Contact Finder Planner Agent'}
          threadId={plannerThreadId}
          entityId={effort?.effort_prefix || ''}
          agentDescription="Directly orchestrate research, prospect discovery, and delegation for this effort."
          store={chatStore}
        />
      }
    />
  )
}

