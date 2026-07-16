export function getAtPath(value: unknown, path: string): unknown {
  if (path === '.' || path === '') return value
  return path.split('.').reduce<unknown>((current, part) => {
    if (current == null || typeof current !== 'object') return undefined
    return (current as Record<string, unknown>)[part]
  }, value)
}

export function setAtPath(value: unknown, path: string, next: unknown): unknown {
  if (path === '.' || path === '') return next
  const parts = path.split('.')
  const clone =
    value && typeof value === 'object' && !Array.isArray(value)
      ? { ...(value as Record<string, unknown>) }
      : {}
  let cursor: Record<string, unknown> = clone
  parts.forEach((part, index) => {
    if (index === parts.length - 1) {
      cursor[part] = next
      return
    }
    const existing = cursor[part]
    const child =
      existing && typeof existing === 'object' && !Array.isArray(existing)
        ? { ...(existing as Record<string, unknown>) }
        : {}
    cursor[part] = child
    cursor = child
  })
  return clone
}

export function parseList(raw: string): string[] {
  return raw
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean)
}
