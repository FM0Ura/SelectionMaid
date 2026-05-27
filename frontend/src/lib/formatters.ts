const fileSizeUnits = ['B', 'KB', 'MB', 'GB', 'TB'] as const

export function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return '0 B'
  }

  const unitIndex = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    fileSizeUnits.length - 1,
  )
  const value = bytes / 1024 ** unitIndex

  if (unitIndex === 0) {
    return `${Math.round(value)} ${fileSizeUnits[unitIndex]}`
  }

  return `${value.toFixed(1)} ${fileSizeUnits[unitIndex]}`
}

export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 1) {
    return '< 1s'
  }

  return `${seconds.toFixed(1)}s`
}

export function formatDate(isoString: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    year: '2-digit',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(isoString))
}

export function formatPageRange(pageStart: number, pageEnd: number): string {
  if (pageStart === pageEnd) {
    return `Pg ${pageStart}`
  }

  return `Pgs ${pageStart}-${pageEnd}`
}

export function slugifyFilename(filename: string): string {
  const base = filename.replace(/\.[^.]+$/, '')
  return base
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}
