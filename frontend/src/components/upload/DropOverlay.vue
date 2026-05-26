<script setup lang="ts">
import { UploadCloud } from 'lucide-vue-next'
import { motion } from 'motion-v'
</script>

<template>
  <motion.div
    data-testid="drop-overlay"
    class="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 rounded-lg border border-primary/60 bg-background/70 text-primary backdrop-blur-md"
    :initial="{ opacity: 0 }"
    :animate="{ opacity: 1 }"
    :transition="{ duration: 0.16 }"
  >
    <UploadCloud class="size-8" aria-hidden="true" />
    <p class="text-sm font-medium">Solte para enviar</p>
  </motion.div>
</template>
