<script setup lang="ts">
import { LoaderCircle } from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps<{
  elapsedSeconds: number
}>()

const formattedElapsed = computed(() => {
  const minutes = Math.floor(props.elapsedSeconds / 60)
  const seconds = props.elapsedSeconds % 60

  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})
</script>

<template>
  <div class="flex w-full items-center justify-center gap-4" aria-live="polite">
    <LoaderCircle class="size-8 shrink-0 animate-spin text-primary" aria-hidden="true" />
    <div class="min-w-0 text-left">
      <p class="font-semibold">Processando documento...</p>
      <p class="mt-1 text-sm text-muted-foreground">
        Tempo decorrido
        <span class="font-mono text-primary">{{ formattedElapsed }}</span>
      </p>
    </div>
  </div>
</template>
