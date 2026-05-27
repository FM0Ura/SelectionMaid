<script setup lang="ts">
import { ArrowLeft, Check, Download } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import type { ExtractionResponse } from '@/types/api'
import { slugifyFilename } from '@/lib/formatters'
import ChunkCard from './ChunkCard.vue'
import MetadataCard from './MetadataCard.vue'

defineProps<{
  data: ExtractionResponse
  elapsedSeconds: number
}>()

defineEmits<{
  reset: []
}>()

const downloaded = ref(false)

function buildMarkdownContent(data: ExtractionResponse): string {
  const meta = data.metadata
  const frontmatter = [
    '---',
    `title: ${meta.title || meta.source_filename}`,
    `language: ${meta.language}`,
    `doc_type: ${meta.doc_type}`,
    `ingested_at: ${meta.ingested_at}`,
    `chunk_count: ${meta.chunk_count}`,
    '---',
    '',
  ].join('\n')

  const chunks = data.chunks.map((chunk, i) => [
    `# Chunk ${i + 1}`,
    `<!-- pages: ${chunk.page_start}-${chunk.page_end} | words: ${chunk.word_count} | section: ${chunk.section_title} -->`,
    '',
    chunk.content,
    '',
    '---',
    '',
  ].join('\n')).join('\n')

  return frontmatter + chunks
}

function downloadAll(data: ExtractionResponse): void {
  const content = buildMarkdownContent(data)
  const filename = `${slugifyFilename(data.metadata.source_filename)}-chunks.md`
  const blob = new Blob([content], { type: 'text/markdown; charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  setTimeout(() => URL.revokeObjectURL(url), 0)
  downloaded.value = true
  setTimeout(() => { downloaded.value = false }, 1500)
}

const chunkListVariants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.07,
    },
  },
}
</script>

<template>
  <section class="w-full max-w-4xl mx-auto space-y-5" aria-label="Resultado da extração">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="space-y-1">
        <p class="text-sm font-medium text-muted-foreground">SelectionMaid</p>
        <h1 class="text-2xl font-semibold leading-tight">Chunks extraídos</h1>
      </div>

      <div class="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          :aria-label="downloaded ? 'Download concluído' : 'Baixar todos os chunks como arquivo Markdown'"
          @click="downloadAll(data)"
        >
          <Check v-if="downloaded" class="text-primary" aria-hidden="true" />
          <Download v-else aria-hidden="true" />
          {{ downloaded ? 'Baixado!' : 'Download .MD' }}
        </Button>

        <Button type="button" variant="outline" aria-label="Fazer novo upload" @click="$emit('reset')">
          <ArrowLeft aria-hidden="true" />
          Novo Upload
        </Button>
      </div>
    </div>

    <MetadataCard :metadata="data.metadata" :elapsed-seconds="elapsedSeconds" />

    <motion.div
      class="space-y-4"
      :variants="chunkListVariants"
      initial="hidden"
      animate="show"
      aria-label="Chunks do documento"
    >
      <ChunkCard v-for="chunk in data.chunks" :key="chunk.chunk_id" :chunk="chunk" />
    </motion.div>
  </section>
</template>
