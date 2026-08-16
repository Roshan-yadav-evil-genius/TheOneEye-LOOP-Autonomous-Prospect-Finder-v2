import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { StateSnapshotList, getNextNodeFromSnapshot } from './state-snapshot-list'
import type { StateSnapshotRead } from '../api/setup-chat-api-client'

describe('StateSnapshotList component grouping', () => {
  it('groups state snapshots by checkpoint_ns and displays group headers', () => {
    const mockSnapshots: StateSnapshotRead[] = [
      {
        step_index: 1,
        checkpoint_id: 'cp-root-1',
        checkpoint_ns: null,
        created_at: '2026-08-15T12:00:00.000Z',
        values: { task: 'Root step 1' },
      },
      {
        step_index: 2,
        checkpoint_id: 'cp-root-2',
        checkpoint_ns: null,
        values: { task: 'Root step 2' },
      },
      {
        step_index: 3,
        checkpoint_id: 'cp-planner-1',
        checkpoint_ns: 'planner:ff010e86-1234',
        created_at: '2026-08-15T12:05:00.000Z',
        values: { planner_chat: ['Plan item'] },
      },
      {
        step_index: 4,
        checkpoint_id: 'cp-planner-2',
        checkpoint_ns: 'planner:ff010e86-1234',
        values: { planner_chat: ['Plan item 2'] },
      },
    ]

    render(<StateSnapshotList snapshots={mockSnapshots} loading={false} />)

    // Verify Root Group Header
    const rootHeader = screen.getByText('🌐 Root / Main Thread')
    expect(rootHeader).toBeInTheDocument()

    // Verify Subagent Group Header
    const subagentHeader = screen.getByText('📦 planner:ff010e86-1234')
    expect(subagentHeader).toBeInTheDocument()

    // Expand groups by clicking header chips
    fireEvent.click(rootHeader)
    fireEvent.click(subagentHeader)

    // Verify Step Badges inside groups
    expect(screen.getByText('Step #1')).toBeInTheDocument()
    expect(screen.getByText('Step #3')).toBeInTheDocument()
  })

  it('inlines tool invocation sub-namespaces within the parent planner group card', () => {
    const mockSnapshots: StateSnapshotRead[] = [
      {
        step_index: 4,
        checkpoint_id: 'cp-p4',
        checkpoint_ns: 'planner:ba207228-50b1',
        values: { task: 'Start planner' },
      },
      {
        step_index: 11,
        checkpoint_id: 'cp-t11',
        checkpoint_ns: 'planner:ba207228-50b1|tools:73bc497a-1203',
        values: { tool_run: 'search_company' },
      },
      {
        step_index: 16,
        checkpoint_id: 'cp-p16',
        checkpoint_ns: 'planner:ba207228-50b1',
        values: { task: 'Resume planner' },
      },
    ]

    render(<StateSnapshotList snapshots={mockSnapshots} loading={false} />)

    // Primary group label should be unified as single parent box
    const groupHeader = screen.getByText('📦 planner:ba207228-50b1')
    expect(groupHeader).toBeInTheDocument()

    // Expand group
    fireEvent.click(groupHeader)

    // Verify tool subagent sub-card header is rendered
    const toolHeader = screen.getByText('🛠️ Subagent Tool: tools:73bc497a-1203')
    expect(toolHeader).toBeInTheDocument()

    // Expand tool group
    fireEvent.click(toolHeader)

    // Verify steps inside outer parent and inner tool sub-card are rendered
    expect(screen.getByText('Step #4')).toBeInTheDocument()
    expect(screen.getByText('Step #11')).toBeInTheDocument()
    expect(screen.getByText('Step #16')).toBeInTheDocument()
  })

  it('triggers onRetryCheckpoint passing the complete config dictionary when Fork & Retry button is clicked', () => {
    const onRetryMock = vi.fn()
    const targetConfig = {
      configurable: {
        thread_id: 'test-thread-123',
        checkpoint_ns: 'planner:ff010e86-1234',
        checkpoint_id: 'cp-target-999',
      },
    }

    const mockSnapshots: StateSnapshotRead[] = [
      {
        step_index: 5,
        config: targetConfig,
        values: { task: 'Target step' },
      },
    ]

    render(
      <StateSnapshotList
        snapshots={mockSnapshots}
        loading={false}
        onRetryCheckpoint={onRetryMock}
      />
    )

    // Expand planner group
    fireEvent.click(screen.getByText('📦 planner:ff010e86-1234'))

    // Expand step #5
    fireEvent.click(screen.getByText('Step #5'))

    // Click Fork & Retry button
    const retryBtn = screen.getByRole('button', { name: '🔁 Fork & Retry' })
    fireEvent.click(retryBtn)

    expect(onRetryMock).toHaveBeenCalledTimes(1)
    expect(onRetryMock).toHaveBeenCalledWith(targetConfig)
  })
})

describe('getNextNodeFromSnapshot helper and UI banner rendering', () => {
  it('resolves next node from channel_values key starting with branch:to: or branch:to_', () => {
    const snapshotWithColon: StateSnapshotRead = {
      step_index: 1,
      checkpoint: {
        channel_values: {
          'branch:to:evaluator': { some: 'data' },
        },
      },
    }
    expect(getNextNodeFromSnapshot(snapshotWithColon)).toEqual({ name: 'evaluator', isComplete: false })

    const snapshotWithUnderscore: StateSnapshotRead = {
      step_index: 2,
      checkpoint: {
        channel_values: {
          'branch:to_researcher': { some: 'data' },
        },
      },
    }
    expect(getNextNodeFromSnapshot(snapshotWithUnderscore)).toEqual({ name: 'researcher', isComplete: false })
  })

  it('resolves next node from pending_writes array containing branch:to: or branch:to_', () => {
    const snapshot: StateSnapshotRead = {
      step_index: 1,
      pending_writes: [
        ['task_id_1', 'branch:to:executor', { payload: 'data' }],
      ],
    }
    expect(getNextNodeFromSnapshot(snapshot)).toEqual({ name: 'executor', isComplete: false })
  })

  it('returns completion status as fallback when no next node or branch channel is found', () => {
    const snapshot: StateSnapshotRead = {
      step_index: 10,
      values: { final_output: 'done' },
      pending_writes: [],
    }
    expect(getNextNodeFromSnapshot(snapshot)).toEqual({
      name: 'Completed / End of Graph',
      isComplete: true,
    })
  })

  it('renders "🎯 Next Node to Execute: <node_name>" when next node exists in expanded card body', () => {
    const mockSnapshots: StateSnapshotRead[] = [
      {
        step_index: 1,
        checkpoint_id: 'cp-1',
        checkpoint: {
          channel_values: {
            'branch:to:planner_agent': null,
          },
        },
        values: { status: 'running' },
      },
    ]

    render(<StateSnapshotList snapshots={mockSnapshots} loading={false} />)

    // Expand group and step
    fireEvent.click(screen.getByText('🌐 Root / Main Thread'))
    fireEvent.click(screen.getByText('Step #1'))

    expect(screen.getByText(/🎯 Next Node to Execute:/i)).toBeInTheDocument()
    expect(screen.getByText('planner_agent')).toBeInTheDocument()
  })

  it('renders "🏁 Status: Execution Complete" when execution is complete in expanded card body', () => {
    const mockSnapshots: StateSnapshotRead[] = [
      {
        step_index: 5,
        checkpoint_id: 'cp-final',
        values: { status: 'done' },
        pending_writes: [],
      },
    ]

    render(<StateSnapshotList snapshots={mockSnapshots} loading={false} />)

    // Expand group and step
    fireEvent.click(screen.getByText('🌐 Root / Main Thread'))
    fireEvent.click(screen.getByText('Step #5'))

    expect(screen.getByText('🏁 Status: Execution Complete')).toBeInTheDocument()
  })
})
