<script setup lang="ts">
import { useDropZone } from '@vueuse/core'
import { FileUp, UploadCloud } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { computed, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useUpload } from '@/composables/useUpload'
import DropOverlay from './DropOverlay.vue'
import ErrorBanner from './ErrorBanner.vue'
import ProcessingCard from './ProcessingCard.vue'

const props = defineProps<{
  upload?: ReturnType<typeof useUpload>
}>()

const upload = props.upload ?? useUpload()
const dropZoneRef = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const acceptedTypes = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/html',
]

const isBusy = computed(() =>
  upload.state.value.status === 'uploading' || upload.state.value.status === 'processing',
)

const isProcessing = computed(() => upload.state.value.status === 'processing')

const { isOverDropZone } = useDropZone(dropZoneRef, {
  multiple: true,
  onDrop(files) {
    handleFiles(files)
  },
})

watch(isOverDropZone, (isOver) => {
  if (!isBusy.value) {
    upload.setDragging(isOver)
  }
})

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  handleFiles(input.files === null ? null : Array.from(input.files))
  input.value = ''
}

function handleFiles(files: File[] | null) {
  if (files === null || files.length === 0) {
    return
  }

  if (files.length > 1) {
    upload.setError('Envie apenas um arquivo por vez.', 'MULTIPLE_FILES')
    return
  }

  void upload.startUpload(files[0])
}
</script>

<template>
  <Card class="group w-full max-w-2xl overflow-hidden">
    <motion.div
      ref="dropZoneRef"
      data-testid="drop-zone"
      layout
      class="relative flex flex-col items-center justify-center gap-6 text-center transition-colors"
      :class="[
        upload.state.value.status === 'dragging' ? 'border-purple-600 backdrop-blur-md bg-purple-950/20' : '',
        isProcessing ? 'min-h-48 p-6' : 'min-h-96 p-8',
      ]"
      :animate="upload.state.value.status === 'dragging'
        ? {
          boxShadow: [
            '0 0 0 0 oklch(0.558 0.243 293 / 0), 0 0 0 0 oklch(0.558 0.243 293 / 0)',
            '0 0 24px 4px oklch(0.558 0.243 293 / 0.2), 0 0 0 2px oklch(0.558 0.243 293 / 0.4)',
            '0 0 0 0 oklch(0.558 0.243 293 / 0), 0 0 0 0 oklch(0.558 0.243 293 / 0)',
          ],
        }
        : { boxShadow: '0 0 0 0 oklch(0.558 0.243 293 / 0)' }"
      :transition="{ duration: 1.4, repeat: upload.state.value.status === 'dragging' ? Infinity : 0, ease: 'easeInOut' }"
    >
      <DropOverlay v-if="upload.state.value.status === 'dragging'" />

      <input
        ref="fileInput"
        class="sr-only"
        type="file"
        :accept="acceptedTypes.join(',')"
        data-testid="file-input"
        @change="handleFileChange"
      >

      <template v-if="upload.state.value.status === 'error'">
        <ErrorBanner :message="upload.state.value.message" @retry="upload.reset" />
      </template>

      <template v-else-if="isProcessing">
        <ProcessingCard :elapsed-seconds="upload.elapsedSeconds.value" />
      </template>

      <template v-else-if="upload.state.value.status === 'uploading'">
        <ProcessingCard :elapsed-seconds="0" />
      </template>

      <template v-else>
        <div class="flex size-16 items-center justify-center rounded-full border border-border bg-muted group-hover:border-purple-600">
          <UploadCloud class="size-8 text-muted-foreground group-hover:text-purple-400" aria-hidden="true" />
        </div>
        <div class="space-y-2">
          <h1 class="text-2xl font-semibold">Envie um documento</h1>
          <p class="max-w-md text-sm text-muted-foreground">
            Arraste um PDF, DOCX ou HTML para começar, ou selecione um arquivo no computador.
          </p>
        </div>
        <Button type="button" size="lg" @click="openFilePicker">
          <FileUp aria-hidden="true" />
          Selecionar arquivo
        </Button>
      </template>
    </motion.div>
  </Card>
</template>
