<script setup lang="ts">
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import { computed } from 'vue'

const props = defineProps<{
  content: string
}>()

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
})

const sanitizedHtml = computed(() => DOMPurify.sanitize(markdown.render(props.content)))
</script>

<template>
  <div
    class="prose prose-invert max-w-none text-foreground prose-headings:text-foreground prose-a:text-primary prose-strong:text-foreground prose-code:text-foreground prose-pre:border prose-pre:border-border prose-pre:bg-muted"
    v-html="sanitizedHtml"
  />
</template>
