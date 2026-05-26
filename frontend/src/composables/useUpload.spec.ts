import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { mapApiError } from '@/api/errors'
import { postIngest } from '@/api/ingest'
import type { ExtractionResponse } from '@/types/api'
import { useUpload } from './useUpload'

vi.mock('@/api/ingest', () => ({
  postIngest: vi.fn(),
}))

vi.mock('@/api/errors', async () => {
  const actual = await vi.importActual<typeof import('@/api/errors')>('@/api/errors')

  return {
    ...actual,
    mapApiError: vi.fn(actual.mapApiError),
  }
})

const postIngestMock = vi.mocked(postIngest)
const mapApiErrorMock = vi.mocked(mapApiError)

const extractionResponse: ExtractionResponse = {
  metadata: {
    doc_id: 'doc-1',
    source_filename: 'paper.pdf',
    title: 'Paper',
    author: 'Author',
    language: 'pt',
    doc_type: 'pdf',
    page_count: 1,
    chunk_count: 1,
    ingested_at: '2026-05-26T00:00:00Z',
  },
  chunks: [
    {
      chunk_id: 'chunk-1',
      content: 'content',
      page_start: 1,
      page_end: 1,
      section_title: 'Intro',
      chunk_index: 0,
      total_chunks: 1,
      word_count: 1,
    },
  ],
}

function pdfFile() {
  return new File(['content'], 'paper.pdf', { type: 'application/pdf' })
}

describe('useUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mapApiErrorMock.mockImplementation((error) =>
      error instanceof Error ? error.message : 'Erro ao processar',
    )
  })

  it('starts in idle state', () => {
    const upload = useUpload()

    expect(upload.state.value).toEqual({ status: 'idle' })
  })

  it('tracks dragging state and returns to idle', () => {
    const upload = useUpload()

    upload.setDragging(true)
    expect(upload.state.value).toEqual({ status: 'dragging' })

    upload.setDragging(false)
    expect(upload.state.value).toEqual({ status: 'idle' })
  })

  it('rejects invalid files before calling the API', async () => {
    const upload = useUpload()
    const file = new File(['content'], 'image.png', { type: 'image/png' })

    await upload.startUpload(file)

    expect(postIngestMock).not.toHaveBeenCalled()
    expect(upload.state.value.status).toBe('error')
  })

  it('allows UI-level errors without calling the API', () => {
    const upload = useUpload()

    upload.setError('Envie apenas um arquivo.', 'MULTIPLE_FILES')

    expect(postIngestMock).not.toHaveBeenCalled()
    expect(upload.state.value).toEqual({
      status: 'error',
      message: 'Envie apenas um arquivo.',
      code: 'MULTIPLE_FILES',
    })
  })

  it('transitions through upload and processing to success', async () => {
    const upload = useUpload()
    let resolveUpload: (response: ExtractionResponse) => void = () => undefined
    postIngestMock.mockReturnValue(
      new Promise<ExtractionResponse>((resolve) => {
        resolveUpload = resolve
      }),
    )

    const promise = upload.startUpload(pdfFile())

    expect(upload.state.value).toEqual({ status: 'processing' })
    resolveUpload(extractionResponse)
    await promise

    expect(upload.state.value).toEqual({
      status: 'success',
      data: extractionResponse,
    })
  })

  it('transitions failed uploads to error with the mapped message', async () => {
    const upload = useUpload()
    const timeout = new DOMException('Timed out', 'AbortError')
    mapApiErrorMock.mockReturnValue('Timeout depois de 130s')
    postIngestMock.mockRejectedValue(timeout)

    await upload.startUpload(pdfFile())

    expect(mapApiErrorMock).toHaveBeenCalledWith(timeout)
    expect(upload.state.value).toEqual({
      status: 'error',
      message: 'Timeout depois de 130s',
    })
  })

  it('resets to idle', async () => {
    const upload = useUpload()
    postIngestMock.mockResolvedValue(extractionResponse)

    await upload.startUpload(pdfFile())
    upload.reset()
    await nextTick()

    expect(upload.state.value).toEqual({ status: 'idle' })
  })
})
