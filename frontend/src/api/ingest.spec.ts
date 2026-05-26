import { afterEach, describe, expect, it, vi } from 'vitest'
import { postIngest } from './ingest'
import type { ExtractionResponse } from '@/types/api'

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

describe('postIngest', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('sends the file as FormData and returns a typed response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(extractionResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const file = new File(['content'], 'paper.pdf', { type: 'application/pdf' })
    const response = await postIngest(file)
    const [, init] = fetchMock.mock.calls[0]

    expect(fetchMock).toHaveBeenCalledWith('/api/ingest', expect.any(Object))
    expect(init.method).toBe('POST')
    expect(init.body).toBeInstanceOf(FormData)
    expect(init.signal).toBeInstanceOf(AbortSignal)
    expect(response.metadata.doc_id).toBe('doc-1')
  })

  it('uses a 130s AbortSignal timeout', async () => {
    const timeoutSpy = vi.spyOn(AbortSignal, 'timeout')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify(extractionResponse))),
    )

    await postIngest(new File(['content'], 'paper.pdf', { type: 'application/pdf' }))

    expect(timeoutSpy).toHaveBeenCalledWith(130000)
  })

  it('throws an ApiResponseError for structured API failures', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: { code: 'UPLOAD-001', message: 'File too large' },
          }),
          { status: 413 },
        ),
      ),
    )

    await expect(
      postIngest(new File(['content'], 'paper.pdf', { type: 'application/pdf' })),
    ).rejects.toMatchObject({
      status: 413,
      code: 'UPLOAD-001',
      message: 'File too large',
    })
  })
})
