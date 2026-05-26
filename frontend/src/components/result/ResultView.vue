<script setup lang="ts">
import { ArrowLeft } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import type { ExtractionResponse } from '@/types/api'
import ChunkCard from './ChunkCard.vue'
import MetadataCard from './MetadataCard.vue'

defineProps<{
  data: ExtractionResponse
  elapsedSeconds: number
}>()

defineEmits<{
  reset: []
}>()
</script>

<template>
  <section class="w-full max-w-4xl space-y-5" aria-label="Resultado da extração">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="space-y-1">
        <p class="text-sm font-medium text-muted-foreground">SelectionMaid</p>
        <h1 class="text-2xl font-semibold leading-tight">Chunks extraídos</h1>
      </div>

      <Button type="button" variant="outline" @click="$emit('reset')">
        <ArrowLeft aria-hidden="true" />
        Novo Upload
      </Button>
    </div>

    <MetadataCard :metadata="data.metadata" :elapsed-seconds="elapsedSeconds" />

    <div class="space-y-4" aria-label="Chunks do documento">
      <ChunkCard v-for="chunk in data.chunks" :key="chunk.chunk_id" :chunk="chunk" />
    </div>
  </section>
</template>
