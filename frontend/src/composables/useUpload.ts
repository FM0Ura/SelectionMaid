import { readonly, ref } from 'vue'
import { mapApiError } from '@/api/errors'
import { postIngest } from '@/api/ingest'
import { validateFile } from '@/lib/validators'
import type { UploadState } from '@/types/api'

export function useUpload() {
  const state = ref<UploadState>({ status: 'idle' })

  function setDragging(isDragging: boolean) {
    state.value = isDragging ? { status: 'dragging' } : { status: 'idle' }
  }

  function reset() {
    state.value = { status: 'idle' }
  }

  async function startUpload(file: File) {
    const validationError = validateFile(file)
    if (validationError !== null) {
      state.value = { status: 'error', message: validationError }
      return
    }

    state.value = { status: 'uploading', progress: 0 }

    try {
      const uploadPromise = postIngest(file)
      state.value = { status: 'processing' }
      const data = await uploadPromise
      state.value = { status: 'success', data }
    } catch (error) {
      state.value = { status: 'error', message: mapApiError(error) }
    }
  }

  return {
    state: readonly(state),
    startUpload,
    setDragging,
    reset,
  }
}
