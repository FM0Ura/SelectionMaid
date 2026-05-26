import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import MarkdownRenderer from './MarkdownRenderer.vue'

describe('MarkdownRenderer', () => {
  it('renders markdown headings and emphasis as HTML', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '# Title\n\nThis is **bold** text.',
      },
    })

    expect(wrapper.find('h1').text()).toBe('Title')
    expect(wrapper.find('strong').text()).toBe('bold')
  })

  it('sanitizes malicious HTML from rendered content', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '<script>alert(1)</script>\n\n# Safe',
      },
    })

    expect(wrapper.html()).not.toContain('<script>')
    expect(wrapper.text()).toContain('Safe')
  })

  it('applies typography classes to the rendered container', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: 'Plain text',
      },
    })

    expect(wrapper.classes()).toEqual(expect.arrayContaining(['prose', 'prose-invert', 'max-w-none']))
  })
})
