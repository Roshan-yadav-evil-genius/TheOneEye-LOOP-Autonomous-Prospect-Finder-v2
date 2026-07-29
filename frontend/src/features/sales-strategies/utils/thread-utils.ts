export function trimThreadId(threadId: string, effortPrefix: string): string {
  if (!threadId) return ''
  let trimmed = threadId
  if (!effortPrefix) return trimmed

  const prefixWithSep = effortPrefix.endsWith('_') ? effortPrefix : `${effortPrefix}_`
  if (trimmed.startsWith(prefixWithSep)) {
    trimmed = trimmed.slice(prefixWithSep.length)
  } else if (trimmed.startsWith(effortPrefix)) {
    trimmed = trimmed.slice(effortPrefix.length).replace(/^[_:]/, '')
  }

  if (trimmed.startsWith('company_finder_')) {
    trimmed = trimmed.slice('company_finder_'.length)
  } else if (trimmed.startsWith('contact_finder_')) {
    trimmed = trimmed.slice('contact_finder_'.length)
  }

  return trimmed || threadId
}

export function formatThreadRoleLabel(trimmedLabel: string, primaryRole: string = 'company_finder') {
  const norm = trimmedLabel.toLowerCase()
  const dbRole = primaryRole.toLowerCase().replace('-', '_')

  if (norm === 'company_finder' || norm === 'contact_finder' || norm === dbRole) {
    return {
      title: trimmedLabel,
      subtitle: 'Primary Agent',
      icon: '🤖',
      badgeClass: 'badge-primary'
    }
  }

  if (norm.startsWith('gpa_') || norm.includes('gpa_') || norm === 'gpa') {
    const numMatch = norm.match(/\d+/)
    const num = numMatch ? numMatch[0] : ''
    return {
      title: trimmedLabel,
      subtitle: `GPA Delegate ${num ? `#${num}` : ''}`.trim(),
      icon: '⚡',
      badgeClass: 'badge-info'
    }
  }

  if (norm === 'brain' || norm.includes('brain')) {
    return {
      title: trimmedLabel,
      subtitle: 'Brain Memory',
      icon: '🧠',
      badgeClass: 'badge-purple'
    }
  }

  if (norm.startsWith('browser') || norm.includes('browser')) {
    const numMatch = norm.match(/\d+/)
    const num = numMatch ? numMatch[0] : ''
    return {
      title: trimmedLabel,
      subtitle: `Browser Worker ${num ? `#${num}` : ''}`.trim(),
      icon: '🌐',
      badgeClass: 'badge-warning'
    }
  }

  return {
    title: trimmedLabel,
    subtitle: 'Subagent Thread',
    icon: '💬',
    badgeClass: 'badge-neutral'
  }
}
