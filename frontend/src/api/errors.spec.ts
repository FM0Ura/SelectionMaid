import { describe, expect, it } from 'vitest'
import { ApiResponseError, mapApiError } from './errors'

describe('mapApiError', () => {
  it('maps AbortError to a 130s timeout message', () => {
    const error = new DOMException('Timed out', 'AbortError')

    expect(mapApiError(error)).toContain('130s')
  })

  it('maps 413 to a file size message', () => {
    const error = new ApiResponseError('too large', 413, 'UPLOAD-001')

    expect(mapApiError(error)).toContain('Arquivo muito grande')
  })

  it('maps 415 to an unsupported format message', () => {
    const error = new ApiResponseError('unsupported', 415, 'EXT-002')

    expect(mapApiError(error)).toContain('Formato não suportado')
  })

  it('uses the API error message for unknown HTTP statuses', () => {
    const error = new ApiResponseError('Falha personalizada', 500, 'EXT-001')

    expect(mapApiError(error)).toBe('Falha personalizada')
  })
})
