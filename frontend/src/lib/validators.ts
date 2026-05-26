const MAX_FILE_BYTES = 50 * 1024 * 1024

const ALLOWED_MIME_TYPES = new Set([
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/html',
])

export function validateFile(file: File): string | null {
  if (file.size > MAX_FILE_BYTES) {
    return 'Arquivo muito grande. O limite máximo é 50MB.'
  }

  if (!ALLOWED_MIME_TYPES.has(file.type)) {
    return 'Formato não suportado. Envie um arquivo PDF, DOCX ou HTML.'
  }

  return null
}

export { ALLOWED_MIME_TYPES, MAX_FILE_BYTES }
