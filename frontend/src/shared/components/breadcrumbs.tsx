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

    const src = item.thumbnailUrl || item.fallbackThumbnailUrl
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
        {src ? (
          <img 
            src={src} 
            alt="" 
            style={{ 
              width: 20, 
              height: 20, 
              borderRadius: '4px', 
              objectFit: 'contain' 
            }} 
            onError={(e) => {
              if (item.fallbackThumbnailUrl && e.currentTarget.src !== item.fallbackThumbnailUrl) {
                e.currentTarget.src = item.fallbackThumbnailUrl
              } else {
                e.currentTarget.style.display = 'none'
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
