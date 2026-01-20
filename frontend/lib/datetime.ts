export function parseApiDate(dateString: string): Date {
  const s = dateString.trim()
  const hasZone = /([zZ]|[+\-]\d{2}:\d{2})$/.test(s)
  if (hasZone) return new Date(s)
  if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(s)) {
    return new Date(s.replace(' ', 'T') + 'Z')
  }
  return new Date(s)
}

export function formatDateTime(dateString: string): string {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
  const d = parseApiDate(dateString)
  try {
    return new Intl.DateTimeFormat(undefined, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: tz,
      timeZoneName: 'short',
    }).format(d)
  } catch {
    try {
      return new Intl.DateTimeFormat(undefined, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: tz,
      }).format(d)
    } catch {
      return d.toLocaleString()
    }
  }
}

export function formatDate(dateString: string): string {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
  const d = parseApiDate(dateString)
  try {
    return new Intl.DateTimeFormat(undefined, {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      timeZone: tz,
    }).format(d)
  } catch {
    return d.toLocaleDateString()
  }
}
