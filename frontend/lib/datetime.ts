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
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'short',
    timeStyle: 'medium',
    timeZone: tz,
    timeZoneName: 'short',
  }).format(parseApiDate(dateString))
}

export function formatDate(dateString: string): string {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeZone: tz,
  }).format(parseApiDate(dateString))
}
