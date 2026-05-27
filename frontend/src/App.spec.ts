import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import App from './App.vue'
import type { ExtractionResponse, UploadState } from './types/api'

const uploadState = ref<UploadState>({ status: 'processing' })
const reset = vi.fn(() => {
  uploadState.value = { status: 'idle' }
})

const extractionResponse: ExtractionResponse = {
  metadata: {
    doc_id: 'doc-1',
    source_filename: 'report.pdf',
    title: 'Quarterly Report',
    author: 'SelectionMaid',
    language: 'pt-BR',
    doc_type: 'pdf',
    page_count: 8,
    chunk_count: 1,
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
      total_chunks: 1,
      word_count: 12,
    },
  ],
}

vi.mock('@/composables/useUpload', () => ({
  useUpload: vi.fn(() => ({
    state: uploadState,
    elapsedSeconds: ref(12),
    startUpload: vi.fn(),
    setDragging: vi.fn(),
    setError: vi.fn(),
    reset,
  })),
}))

vi.mock('@vueuse/core', async () => {
  const actual = await vi.importActual<typeof import('@vueuse/core')>('@vueuse/core')

  return {
    ...actual,
    useDropZone: vi.fn(() => ({
      files: ref(null),
      isOverDropZone: ref(false),
    })),
  }
})

describe('App', () => {
  it('renders skeleton chunks while processing', () => {
    uploadState.value = { status: 'processing' }
    const wrapper = mount(App)

    expect(wrapper.findAllComponents({ name: 'SkeletonChunk' })).toHaveLength(4)
    expect(wrapper.text()).toContain('Processando documento')
  })

  it('hides skeleton chunks outside processing', () => {
    uploadState.value = { status: 'idle' }
    const wrapper = mount(App)

    expect(wrapper.findAllComponents({ name: 'SkeletonChunk' })).toHaveLength(0)
  })

  it('renders result view and hides drop zone for success state', () => {
    uploadState.value = { status: 'success', data: extractionResponse }
    const wrapper = mount(App)

    expect(wrapper.findComponent({ name: 'ResultView' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'DropZone' }).exists()).toBe(false)
    expect(wrapper.text()).toContain('Quarterly Report')
  })

  it('resets upload state from the result view', async () => {
    uploadState.value = { status: 'success', data: extractionResponse }
    const wrapper = mount(App)

    await wrapper.get('[aria-label="Fazer novo upload"]').trigger('click')

    expect(reset).toHaveBeenCalled()
  })
})
