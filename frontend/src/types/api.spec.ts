import { describe, expect, it } from 'vitest'
import type { UploadState } from './api'

describe('UploadState', () => {
  it('models success with extraction data', () => {
    const state: UploadState = {
      status: 'success',
      data: {
        metadata: {
          doc_id: 'doc-1',
          source_filename: 'paper.pdf',
          title: 'Paper',
          author: 'Author',
          language: 'pt',
          doc_type: 'pdf',
          page_count: 2,
          chunk_count: 1,
          ingested_at: '2026-05-26T00:00:00Z',
        },
        chunks: [
          {
            chunk_id: 'chunk-1',
            content: 'Hello',
            page_start: 1,
            page_end: 1,
            section_title: 'Intro',
            chunk_index: 0,
            total_chunks: 1,
            word_count: 1,
          },
        ],
      },
    }

    expect(state.status).toBe('success')
    expect(state.data.chunks).toHaveLength(1)
  })
})
