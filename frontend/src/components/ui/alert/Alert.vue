<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div
    role="alert"
    data-slot="alert"
    :class="cn('relative w-full rounded-lg border border-border bg-card px-4 py-3 text-sm text-card-foreground', props.class)"
  >
    <slot />
  </div>
</template>
