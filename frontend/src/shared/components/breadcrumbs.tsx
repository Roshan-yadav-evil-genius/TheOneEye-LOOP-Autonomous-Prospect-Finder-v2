import { Link } from 'react-router-dom'

export type BreadcrumbItem = {
  label: string
  to?: string
  thumbnailUrl?: string | null
  fallbackThumbnailUrl?: string
}

export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  if (items.length === 0) return null

  const renderLabel = (item: BreadcrumbItem) => {
    const hasIcon = item.thumbnailUrl !== undefined || item.fallbackThumbnailUrl !== undefined
    if (!hasIcon) return item.label

    const rawSrc = item.thumbnailUrl || item.fallbackThumbnailUrl
    const src = rawSrc ? (rawSrc.startsWith('http') || rawSrc.startsWith('data:') ? rawSrc : rawSrc) : ''

    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
        {src ? (
          <img 
            src={src} 
            alt="" 
            style={{ 
              width: 18, 
              height: 18, 
              borderRadius: '4px', 
              objectFit: 'cover' 
            }} 
            onError={(e) => {
              const target = e.currentTarget
              if (item.fallbackThumbnailUrl && !target.dataset.fallbackTried) {
                target.dataset.fallbackTried = 'true'
                target.src = item.fallbackThumbnailUrl
              } else {
                target.style.display = 'none'
              }
            }}
          />
        ) : null}
        {item.label}
      </span>
    )
  }

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol className="breadcrumbs__list">
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          return (
            <li key={`${item.label}-${index}`} className="breadcrumbs__item">
              {item.to && !isLast ? (
                <Link className="breadcrumbs__link" to={item.to}>
                  {renderLabel(item)}
                </Link>
              ) : (
                <span className="breadcrumbs__current" aria-current={isLast ? 'page' : undefined}>
                  {renderLabel(item)}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
