<script setup lang="ts">
import { AnimatePresence, motion } from 'motion-v'
import DropZone from '@/components/upload/DropZone.vue'
import ResultView from '@/components/result/ResultView.vue'
import SkeletonChunk from '@/components/upload/SkeletonChunk.vue'
import { useUpload } from '@/composables/useUpload'

const upload = useUpload()
</script>

<template>
  <main class="flex min-h-screen flex-col items-center justify-center gap-8 bg-background px-6 py-10 text-foreground">
    <AnimatePresence mode="wait">
      <motion.div
        v-if="upload.state.value.status !== 'success'"
        key="upload-view"
        class="flex w-full flex-col items-center gap-8"
        :initial="{ opacity: 0 }"
        :animate="{ opacity: 1 }"
        :exit="{ opacity: 0 }"
        :transition="{ duration: 0.3 }"
      >
        <section class="w-full max-w-2xl space-y-3 text-center">
          <p class="text-sm font-medium text-muted-foreground">SelectionMaid</p>
          <h1 class="text-3xl font-semibold leading-tight bg-gradient-to-r from-purple-400 to-white bg-clip-text text-transparent">Transforme documentos em chunks Markdown</h1>
        </section>

        <DropZone :upload="upload" />

        <motion.section
          v-if="upload.state.value.status === 'processing'"
          class="mt-2 w-full max-w-2xl space-y-4"
          :initial="{ opacity: 0, y: 20 }"
          :animate="{ opacity: 1, y: 0 }"
          :transition="{ duration: 0.24 }"
          aria-label="Prévia dos chunks em processamento"
        >
          <SkeletonChunk v-for="index in 4" :key="index" />
        </motion.section>
      </motion.div>

      <motion.div
        v-else-if="upload.state.value.status === 'success'"
        key="result-view"
        class="w-full"
        :initial="{ opacity: 0 }"
        :animate="{ opacity: 1 }"
        :exit="{ opacity: 0 }"
        :transition="{ duration: 0.3 }"
      >
        <ResultView
          :data="upload.state.value.data"
          :elapsed-seconds="upload.elapsedSeconds.value"
          @reset="upload.reset()"
        />
      </motion.div>
    </AnimatePresence>
  </main>
</template>
