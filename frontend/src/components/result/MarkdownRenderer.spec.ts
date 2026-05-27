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

  it('wraps tables in overflow-x-auto div', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '| A | B |\n|---|---|\n| 1 | 2 |' },
    })
    expect(wrapper.find('.overflow-x-auto').exists()).toBe(true)
    expect(wrapper.find('.overflow-x-auto table').exists()).toBe(true)
  })

  it('adds target=_blank and rel=noopener on links', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '[Link](https://example.com)' },
    })
    const anchor = wrapper.find('a')
    expect(anchor.attributes('target')).toBe('_blank')
    expect(anchor.attributes('rel')).toBe('noopener noreferrer')
  })

  it('applies syntax highlight class to fenced code blocks', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '```python\nprint("hello")\n```' },
    })
    expect(wrapper.find('code.hljs').exists()).toBe(true)
  })
})
