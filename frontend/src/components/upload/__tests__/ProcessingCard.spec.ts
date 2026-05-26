import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProcessingCard from '../ProcessingCard.vue'

describe('ProcessingCard', () => {
  it('formats elapsed seconds as MM:SS', () => {
    const wrapper = mount(ProcessingCard, {
      props: { elapsedSeconds: 65 },
    })

    expect(wrapper.text()).toContain('01:05')
  })

  it('renders an accessible processing status', () => {
    const wrapper = mount(ProcessingCard, {
      props: { elapsedSeconds: 3 },
    })

    expect(wrapper.attributes('aria-live')).toBe('polite')
    expect(wrapper.text()).toContain('Processando documento')
  })
})
