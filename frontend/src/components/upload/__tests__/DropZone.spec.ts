import { mount } from '@vue/test-utils'
import type { ShallowRef } from 'vue'
import { ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useUpload } from '@/composables/useUpload'
import type { UploadState } from '@/types/api'
import DropZone from '../DropZone.vue'

type DropOptions = {
  onDrop?: (files: File[] | null, event: DragEvent) => void
}

const uploadState = ref<UploadState>({ status: 'idle' })
const startUpload = vi.fn()
const setDragging = vi.fn()
const setError = vi.fn()
const elapsedSeconds = ref(0)
const reset = vi.fn(() => {
  uploadState.value = { status: 'idle' }
})
const isOverDropZone = ref(false)
let dropOptions: DropOptions = {}

vi.mock('@/composables/useUpload', () => ({
  useUpload: vi.fn(() => ({
    state: uploadState,
    elapsedSeconds,
    startUpload,
    setDragging,
    setError,
    reset,
  })),
}))

vi.mock('@vueuse/core', async () => {
  const actual = await vi.importActual<typeof import('@vueuse/core')>('@vueuse/core')

  return {
    ...actual,
    useDropZone: vi.fn((_target: unknown, options: DropOptions) => {
      dropOptions = options
      return {
        files: ref(null) as ShallowRef<File[] | null>,
        isOverDropZone,
      }
    }),
  }
})

function pdfFile(name = 'paper.pdf') {
  return new File(['content'], name, { type: 'application/pdf' })
}

describe('DropZone', () => {
  beforeEach(() => {
    uploadState.value = { status: 'idle' }
    elapsedSeconds.value = 0
    isOverDropZone.value = false
    dropOptions = {}
    vi.clearAllMocks()
  })

  it('renders the welcome state by default', () => {
    const wrapper = mount(DropZone)

    expect(useUpload).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Envie um documento')
    expect(wrapper.text()).toContain('Selecionar arquivo')
  })

  it('renders ErrorBanner for error state', () => {
    uploadState.value = {
      status: 'error',
      message: 'Formato não suportado.',
    }

    const wrapper = mount(DropZone)

    expect(wrapper.text()).toContain('Formato não suportado.')
    expect(wrapper.text()).toContain('Tentar novamente')
  })

  it('renders DropOverlay for dragging state', () => {
    uploadState.value = { status: 'dragging' }

    const wrapper = mount(DropZone)

    expect(wrapper.find('[data-testid="drop-overlay"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Solte para enviar')
  })

  it('renders compact processing feedback with elapsed time', () => {
    uploadState.value = { status: 'processing' }
    elapsedSeconds.value = 65

    const wrapper = mount(DropZone)

    expect(wrapper.get('[data-testid="drop-zone"]').classes()).toContain('min-h-48')
    expect(wrapper.text()).toContain('Processando documento')
    expect(wrapper.text()).toContain('01:05')
    expect(wrapper.find('[data-testid="file-input"]').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('Selecionar arquivo')
  })

  it('starts upload when a single file is dropped', () => {
    mount(DropZone)
    const file = pdfFile()

    dropOptions.onDrop?.([file], new Event('drop') as DragEvent)

    expect(startUpload).toHaveBeenCalledWith(file)
    expect(setError).not.toHaveBeenCalled()
  })

  it('blocks multiple files dropped at once', () => {
    mount(DropZone)

    dropOptions.onDrop?.(
      [pdfFile('a.pdf'), pdfFile('b.pdf')],
      new Event('drop') as DragEvent,
    )

    expect(startUpload).not.toHaveBeenCalled()
    expect(setError).toHaveBeenCalledWith('Envie apenas um arquivo por vez.', 'MULTIPLE_FILES')
  })

  it('starts upload when a file is selected manually', async () => {
    const wrapper = mount(DropZone)
    const input = wrapper.get<HTMLInputElement>('[data-testid="file-input"]')
    const file = pdfFile()

    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true,
    })
    await input.trigger('change')

    expect(startUpload).toHaveBeenCalledWith(file)
  })

  it('syncs drag-over state into useUpload', async () => {
    mount(DropZone)

    isOverDropZone.value = true
    await Promise.resolve()

    expect(setDragging).toHaveBeenCalledWith(true)
  })
})
