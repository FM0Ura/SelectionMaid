import type { ExtractionResponse } from '@/types/api'
import { ApiResponseError } from './errors'

type ErrorBody = {
  error?: {
    code?: string
    message?: string
  }
  detail?: string
}

export async function postIngest(file: File): Promise<ExtractionResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/ingest', {
    method: 'POST',
    body: formData,
    signal: AbortSignal.timeout(130000),
  })

  if (!response.ok) {
    const errorBody = await parseErrorBody(response)
    const message =
      errorBody.error?.message ??
      errorBody.detail ??
      'Não foi possível processar o documento.'

    throw new ApiResponseError(message, response.status, errorBody.error?.code)
  }

  return response.json() as Promise<ExtractionResponse>
}

async function parseErrorBody(response: Response): Promise<ErrorBody> {
  try {
    return (await response.json()) as ErrorBody
  } catch {
    return {}
  }
}
