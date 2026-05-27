<script setup lang="ts">
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import type { Token, Options, Renderer } from 'markdown-it'
import highlightjs from 'markdown-it-highlightjs'
import 'highlight.js/styles/github-dark.css'
import { computed } from 'vue'

const props = defineProps<{
  content: string
}>()

// Module-scope instance — must stay outside setup() to avoid recreation on each render
const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
}).use(highlightjs, { auto: true, code: true, inline: false })

// D-13: target="_blank" on all links
const defaultLinkOpen = markdown.renderer.rules.link_open
  || function (tokens: Token[], idx: number, options: Options, _env: unknown, self: Renderer) {
      return self.renderToken(tokens, idx, options)
    }

markdown.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen(tokens, idx, options, env, self)
}

// D-11: wrap tables in overflow-x-auto div
markdown.renderer.rules.table_open = () => '<div class="overflow-x-auto"><table>'
markdown.renderer.rules.table_close = () => '</table></div>'

// ADD_ATTR allows 'target' which is not in DOMPurify's DEFAULT_ALLOWED_ATTR
// This is safe: target="_blank" cannot cause XSS; rel="noopener noreferrer" is also preserved
const sanitizedHtml = computed(() =>
  DOMPurify.sanitize(markdown.render(props.content), { ADD_ATTR: ['target'] }),
)
</script>

<template>
  <div
    class="prose prose-invert prose-sm max-w-none text-foreground prose-headings:text-foreground prose-a:text-purple-400 prose-a:no-underline prose-a:hover:underline prose-strong:text-foreground prose-code:bg-purple-950/40 prose-code:text-purple-200 prose-code:rounded prose-code:px-1 prose-code:before:content-none prose-code:after:content-none prose-pre:bg-purple-950/60 prose-pre:border prose-pre:border-purple-900/40 prose-table:border prose-table:border-purple-900/40 prose-thead:bg-purple-950/60 prose-img:max-w-full prose-img:h-auto"
    v-html="sanitizedHtml"
  />
</template>
