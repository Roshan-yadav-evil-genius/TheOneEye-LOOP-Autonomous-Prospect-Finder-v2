import type { KeyboardEvent, MouseEvent, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { Badge } from './design-system'
import { EditIcon, IconLink, IconButton, TrashIcon } from './icon-button'

export function EntityList({ children }: { children: ReactNode }) {
  return <div className="entity-list">{children}</div>
}

export function EntityListItem({
  title,
  meta,
  to,
  editTo,
  onEdit,
  editLabel,
  onDelete,
  deleteLabel,
  badge,
  badgeTone = 'info',
  thumbnailUrl,
}: {
  title: string
  meta: ReactNode
  to: string
  editTo?: string
  onEdit?: () => void
  editLabel?: string
  onDelete?: () => void
  deleteLabel?: string
  badge?: string
  badgeTone?: 'info' | 'success' | 'danger' | 'warning'
  thumbnailUrl?: string
}) {
  const navigate = useNavigate()

  const open = () => {
    void navigate(to)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      open()
    }
  }

  const stopAction = (event: MouseEvent) => {
    event.stopPropagation()
  }

  return (
    <article
      className="entity-list-item"
      role="link"
      tabIndex={0}
      onClick={open}
      onKeyDown={onKeyDown}
      aria-label={`Open ${title}`}
    >
      {thumbnailUrl ? (
        <div className="entity-list-item__thumbnail">
          <img src={thumbnailUrl} alt={title} />
        </div>
      ) : null}
      <div className="entity-list-item__body">
        <div className="entity-list-item__title-row">
          <h2 className="entity-list-item__title">{title}</h2>
          {badge ? <Badge tone={badgeTone}>{badge}</Badge> : null}
        </div>
        <div className="entity-list-item__meta muted">{meta}</div>
      </div>
      {editTo || onEdit || onDelete ? (
        <div className="entity-list-item__actions" onClick={stopAction}>
          {editTo ? (
            <IconLink to={editTo} label={editLabel ?? `Edit ${title}`} onClick={stopAction}>
              <EditIcon />
            </IconLink>
          ) : onEdit ? (
            <IconButton label={editLabel ?? `Edit ${title}`} onClick={(e) => { stopAction(e); onEdit(); }}>
              <EditIcon />
            </IconButton>
          ) : null}
          {onDelete ? (
            <IconButton
              label={deleteLabel ?? `Delete ${title}`}
              className="delete-button"
              onClick={(e) => {
                stopAction(e)
                onDelete()
              }}
            >
              <TrashIcon />
            </IconButton>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}
