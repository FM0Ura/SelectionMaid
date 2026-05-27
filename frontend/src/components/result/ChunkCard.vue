<script setup lang="ts">
import { useClipboard } from '@vueuse/core'
import { Check, Copy, Download } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { computed, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { formatPageRange, slugifyFilename } from '@/lib/formatters'
import type { Chunk } from '@/types/api'
import MarkdownRenderer from './MarkdownRenderer.vue'

const props = defineProps<{
  chunk: Chunk
}>()

const { copy, copied } = useClipboard({ copiedDuring: 2000 })

const title = computed(() => props.chunk.section_title || `Chunk ${props.chunk.chunk_index + 1}`)
const pageRange = computed(() => formatPageRange(props.chunk.page_start, props.chunk.page_end))

const chunkVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
}

async function copyChunk() {
  await copy(props.chunk.content)
}

const chunkDownloaded = ref(false)

function downloadChunk(): void {
  const sectionSlug = props.chunk.section_title
    ? slugifyFilename(props.chunk.section_title)
    : `section-${props.chunk.chunk_index + 1}`
  const filename = `chunk-${props.chunk.chunk_index + 1}-${sectionSlug}.md`
  const blob = new Blob([props.chunk.content], { type: 'text/markdown; charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  setTimeout(() => URL.revokeObjectURL(url), 0)
  chunkDownloaded.value = true
  setTimeout(() => {
    chunkDownloaded.value = false
  }, 1500)
}
</script>

<template>
  <motion.div :variants="chunkVariants">
    <Card class="w-full overflow-hidden bg-white/5 backdrop-blur-md border border-purple-900/40 transition-shadow duration-200 hover:shadow-[0_0_20px_2px_rgba(147,51,234,0.3)]">
      <div class="flex flex-col gap-4 border-b border-purple-900/40 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div class="min-w-0 space-y-1">
          <p class="text-xs font-medium uppercase text-muted-foreground">
            Chunk {{ chunk.chunk_index + 1 }} de {{ chunk.total_chunks }}
          </p>
          <h3 class="break-words text-base font-semibold">{{ title }}</h3>
          <div class="flex flex-wrap gap-2 text-xs text-muted-foreground">
            <span>{{ pageRange }}</span>
            <span aria-hidden="true">/</span>
            <span>{{ chunk.word_count }} palavras</span>
          </div>
        </div>

        <div class="flex items-center gap-2 self-start">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            :aria-label="chunkDownloaded ? 'Chunk baixado' : 'Baixar chunk como Markdown'"
            @click="downloadChunk"
          >
            <Check v-if="chunkDownloaded" class="text-primary" aria-hidden="true" />
            <Download v-else aria-hidden="true" />
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            :aria-label="copied ? 'Texto copiado' : 'Copiar texto do chunk'"
            @click="copyChunk"
          >
            <Check v-if="copied" class="text-primary" aria-hidden="true" />
            <Copy v-else aria-hidden="true" />
            <span>{{ copied ? 'Copied!' : 'Copiar' }}</span>
          </Button>
        </div>
      </div>

      <div class="p-4">
        <div class="max-h-[400px] overflow-y-auto">
          <MarkdownRenderer :content="chunk.content" />
        </div>
      </div>
    </Card>
  </motion.div>
</template>
