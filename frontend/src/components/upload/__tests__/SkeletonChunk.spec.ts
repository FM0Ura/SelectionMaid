import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SkeletonChunk from '../SkeletonChunk.vue'

describe('SkeletonChunk', () => {
  it('renders shimmer placeholder lines', () => {
    const wrapper = mount(SkeletonChunk)
    const placeholders = wrapper.findAll('[data-slot="skeleton"]')

    expect(placeholders.length).toBeGreaterThanOrEqual(3)
    expect(wrapper.html()).toContain('shimmer-gradient')
    expect(wrapper.html()).toContain('animate-shimmer')
  })
})
