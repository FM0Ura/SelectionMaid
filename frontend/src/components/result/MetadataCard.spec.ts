import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { DocumentMetadata } from '@/types/api'
import MetadataCard from './MetadataCard.vue'

const metadata: DocumentMetadata = {
  doc_id: 'doc-1',
  source_filename: 'contract.pdf',
  title: 'Service Contract',
  author: 'SelectionMaid',
  language: 'pt-BR',
  doc_type: 'pdf',
  page_count: 12,
  chunk_count: 4,
  ingested_at: '2026-05-26T15:30:00.000Z',
}

describe('MetadataCard', () => {
  it('displays document metadata and processing time', () => {
    const wrapper = mount(MetadataCard, {
      props: {
        metadata,
        elapsedSeconds: 1.5,
      },
    })

    expect(wrapper.text()).toContain('Service Contract')
    expect(wrapper.text()).toContain('PDF')
    expect(wrapper.text()).toContain('pt-BR')
    expect(wrapper.text()).toContain('12 páginas')
    expect(wrapper.text()).toContain('4 chunks')
    expect(wrapper.text()).toContain('1.5s')
  })

  it('falls back to the filename when title is missing', () => {
    const wrapper = mount(MetadataCard, {
      props: {
        metadata: { ...metadata, title: '' },
        elapsedSeconds: 0.5,
      },
    })

    expect(wrapper.text()).toContain('contract.pdf')
    expect(wrapper.text()).toContain('< 1s')
  })
})
