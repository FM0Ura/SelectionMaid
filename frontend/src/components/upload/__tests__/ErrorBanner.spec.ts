import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ErrorBanner from '../ErrorBanner.vue'

describe('ErrorBanner', () => {
  it('displays the provided message', () => {
    const wrapper = mount(ErrorBanner, {
      props: { message: 'Formato não suportado.' },
    })

    expect(wrapper.text()).toContain('Formato não suportado.')
  })

  it('emits retry when the retry button is clicked', async () => {
    const wrapper = mount(ErrorBanner, {
      props: { message: 'Tente novamente.' },
    })

    await wrapper.get('button').trigger('click')

    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
