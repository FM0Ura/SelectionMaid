<script setup lang="ts">
import { useClipboard } from '@vueuse/core'
import { Check, Copy } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { formatPageRange } from '@/lib/formatters'
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
</script>

<template>
  <motion.div :variants="chunkVariants">
    <Card class="w-full overflow-hidden">
      <div class="flex flex-col gap-4 border-b border-border p-4 sm:flex-row sm:items-center sm:justify-between">
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

        <Button
          type="button"
          variant="outline"
          size="sm"
          class="self-start"
          :aria-label="copied ? 'Texto copiado' : 'Copiar texto do chunk'"
          @click="copyChunk"
        >
          <Check v-if="copied" class="text-primary" aria-hidden="true" />
          <Copy v-else aria-hidden="true" />
          <span>{{ copied ? 'Copied!' : 'Copiar' }}</span>
        </Button>
      </div>

      <div class="p-4">
        <MarkdownRenderer :content="chunk.content" />
      </div>
    </Card>
  </motion.div>
</template>
