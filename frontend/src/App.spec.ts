import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import App from './App.vue'
import type { UploadState } from './types/api'

const uploadState = ref<UploadState>({ status: 'processing' })

vi.mock('@/composables/useUpload', () => ({
  useUpload: vi.fn(() => ({
    state: uploadState,
    elapsedSeconds: ref(12),
    startUpload: vi.fn(),
    setDragging: vi.fn(),
    setError: vi.fn(),
    reset: vi.fn(),
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
})
