<script setup lang="ts">
import { useDropZone } from '@vueuse/core'
import { FileUp, LoaderCircle, UploadCloud } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { computed, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useUpload } from '@/composables/useUpload'
import DropOverlay from './DropOverlay.vue'
import ErrorBanner from './ErrorBanner.vue'

const upload = useUpload()
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
  <Card class="w-full max-w-2xl overflow-hidden">
    <motion.div
      ref="dropZoneRef"
      data-testid="drop-zone"
      class="relative flex min-h-96 flex-col items-center justify-center gap-6 p-8 text-center transition-colors"
      :class="upload.state.value.status === 'dragging' ? 'border-primary' : ''"
      :animate="upload.state.value.status === 'dragging'
        ? {
          boxShadow: [
            '0 0 0 0 oklch(0.922 0 0 / 0)',
            '0 0 0 8px oklch(0.922 0 0 / 0.12)',
            '0 0 0 0 oklch(0.922 0 0 / 0)',
          ],
        }
        : { boxShadow: '0 0 0 0 oklch(0.922 0 0 / 0)' }"
      :transition="{ duration: 1.2, repeat: upload.state.value.status === 'dragging' ? Infinity : 0 }"
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

      <template v-else-if="isBusy">
        <LoaderCircle class="size-10 animate-spin text-primary" aria-hidden="true" />
        <div class="space-y-2">
          <h1 class="text-xl font-semibold">Processando documento</h1>
          <p class="max-w-md text-sm text-muted-foreground">
            O arquivo foi enviado. O SelectionMaid está preparando os chunks Markdown.
          </p>
        </div>
      </template>

      <template v-else>
        <div class="flex size-16 items-center justify-center rounded-full border border-border bg-muted">
          <UploadCloud class="size-8 text-muted-foreground" aria-hidden="true" />
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
