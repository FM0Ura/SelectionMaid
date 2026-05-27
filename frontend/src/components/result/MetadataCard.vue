<script setup lang="ts">
import { FileText } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { computed } from 'vue'
import { Card } from '@/components/ui/card'
import { formatDate, formatDuration } from '@/lib/formatters'
import type { DocumentMetadata } from '@/types/api'

const props = defineProps<{
  metadata: DocumentMetadata
  elapsedSeconds: number
}>()

const displayTitle = computed(() => props.metadata.title || props.metadata.source_filename)
const displayType = computed(() => props.metadata.doc_type.toUpperCase())
</script>

<template>
  <motion.div
    layout-id="metadata-card"
    :transition="{ type: 'spring', stiffness: 260, damping: 30 }"
  >
    <Card class="w-full p-5 bg-white/5 backdrop-blur-md border border-purple-900/40">
      <div class="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div class="min-w-0 space-y-2">
          <div class="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText class="size-4" aria-hidden="true" />
            <span>Resultado extraído</span>
          </div>
          <h2 class="break-words text-xl font-semibold leading-tight">{{ displayTitle }}</h2>
          <p class="break-words text-sm text-muted-foreground">{{ metadata.source_filename }}</p>
        </div>

        <dl class="grid grid-cols-2 gap-3 text-sm sm:min-w-72">
          <div class="rounded-md border border-border bg-muted/30 p-3">
            <dt class="text-muted-foreground">Tipo</dt>
            <dd class="mt-1 font-medium">{{ displayType }}</dd>
          </div>
          <div class="rounded-md border border-border bg-muted/30 p-3">
            <dt class="text-muted-foreground">Idioma</dt>
            <dd class="mt-1 font-medium">{{ metadata.language }}</dd>
          </div>
          <div class="rounded-md border border-border bg-muted/30 p-3">
            <dt class="text-muted-foreground">Páginas</dt>
            <dd class="mt-1 font-medium">{{ metadata.page_count }} páginas</dd>
          </div>
          <div class="rounded-md border border-border bg-muted/30 p-3">
            <dt class="text-muted-foreground">Chunks</dt>
            <dd class="mt-1 font-medium">{{ metadata.chunk_count }} chunks</dd>
          </div>
          <div class="rounded-md border border-border bg-muted/30 p-3">
            <dt class="text-muted-foreground">Processamento</dt>
            <dd class="mt-1 font-medium">{{ formatDuration(elapsedSeconds) }}</dd>
          </div>
          <div class="rounded-md border border-border bg-muted/30 p-3">
            <dt class="text-muted-foreground">Ingestão</dt>
            <dd class="mt-1 font-medium">{{ formatDate(metadata.ingested_at) }}</dd>
          </div>
        </dl>
      </div>
    </Card>
  </motion.div>
</template>
