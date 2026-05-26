export class ApiResponseError extends Error {
  readonly status: number
  readonly code?: string

  constructor(message: string, status: number, code?: string) {
    super(message)
    this.name = 'ApiResponseError'
    this.status = status
    this.code = code
  }
}

export function mapApiError(error: unknown): string {
  if (isAbortError(error)) {
    return 'O processamento excedeu o limite de 130s. Tente novamente com um documento menor ou menos complexo.'
  }

  if (isApiError(error)) {
    switch (error.status) {
      case 413:
        return 'Arquivo muito grande. O limite máximo é 50MB.'
      case 415:
        return 'Formato não suportado. Envie um arquivo PDF, DOCX ou HTML.'
      case 422:
        return 'O conteúdo do arquivo parece inválido ou corrompido.'
      case 504:
        return 'O processamento excedeu o limite de 130s. Tente novamente com um documento menor ou menos complexo.'
      default:
        return error.message || 'Não foi possível processar o documento.'
    }
  }

  if (error instanceof Error) {
    return error.message || 'Não foi possível processar o documento.'
  }

  return 'Não foi possível processar o documento.'
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

function isApiError(error: unknown): error is ApiResponseError {
  return error instanceof ApiResponseError
}
