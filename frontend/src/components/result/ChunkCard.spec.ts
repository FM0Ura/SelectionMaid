import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import type { Chunk } from '@/types/api'
import ChunkCard from './ChunkCard.vue'

const copied = ref(false)
const copy = vi.fn(async () => {
  copied.value = true
})

vi.mock('@vueuse/core', async () => {
  const actual = await vi.importActual<typeof import('@vueuse/core')>('@vueuse/core')

  return {
    ...actual,
    useClipboard: vi.fn(() => ({
      copy,
      copied,
      isSupported: ref(true),
    })),
  }
})

const chunk: Chunk = {
  chunk_id: 'chunk-1',
  content: '# Section\n\nThis is **bold** text.',
  page_start: 1,
  page_end: 2,
  section_title: 'Overview',
  chunk_index: 0,
  total_chunks: 3,
  word_count: 42,
}

describe('ChunkCard', () => {
  beforeEach(() => {
    copied.value = false
    copy.mockClear()
  })

  it('renders chunk metadata and markdown content', () => {
    const wrapper = mount(ChunkCard, {
      props: { chunk },
    })

    expect(wrapper.text()).toContain('Overview')
    expect(wrapper.text()).toContain('Chunk 1 de 3')
    expect(wrapper.text()).toContain('Pgs 1-2')
    expect(wrapper.text()).toContain('42 palavras')
    expect(wrapper.find('h1').text()).toBe('Section')
    expect(wrapper.find('strong').text()).toBe('bold')
  })

  it('copies raw chunk text and displays copied feedback', async () => {
    const wrapper = mount(ChunkCard, {
      props: { chunk },
    })

    await wrapper.get('button').trigger('click')

    expect(copy).toHaveBeenCalledWith(chunk.content)
    expect(wrapper.text()).toContain('Copied!')
  })
})
