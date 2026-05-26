import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { ExtractionResponse } from '@/types/api'
import ResultView from './ResultView.vue'

const data: ExtractionResponse = {
  metadata: {
    doc_id: 'doc-1',
    source_filename: 'report.pdf',
    title: 'Quarterly Report',
    author: 'SelectionMaid',
    language: 'pt-BR',
    doc_type: 'pdf',
    page_count: 8,
    chunk_count: 2,
    ingested_at: '2026-05-26T15:30:00.000Z',
  },
  chunks: [
    {
      chunk_id: 'chunk-1',
      content: '# First chunk',
      page_start: 1,
      page_end: 1,
      section_title: 'Intro',
      chunk_index: 0,
      total_chunks: 2,
      word_count: 12,
    },
    {
      chunk_id: 'chunk-2',
      content: 'Second **chunk**',
      page_start: 2,
      page_end: 3,
      section_title: 'Details',
      chunk_index: 1,
      total_chunks: 2,
      word_count: 20,
    },
  ],
}

describe('ResultView', () => {
  it('renders metadata and all chunk cards', () => {
    const wrapper = mount(ResultView, {
      props: {
        data,
        elapsedSeconds: 3,
      },
    })

    expect(wrapper.text()).toContain('Quarterly Report')
    expect(wrapper.findAllComponents({ name: 'ChunkCard' })).toHaveLength(2)
    expect(wrapper.text()).toContain('Intro')
    expect(wrapper.text()).toContain('Details')
  })

  it('emits reset when the new upload button is clicked', async () => {
    const wrapper = mount(ResultView, {
      props: {
        data,
        elapsedSeconds: 3,
      },
    })

    await wrapper.get('button').trigger('click')

    expect(wrapper.emitted('reset')).toHaveLength(1)
  })
})
