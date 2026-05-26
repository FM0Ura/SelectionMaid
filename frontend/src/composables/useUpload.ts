import { useIntervalFn } from '@vueuse/core'
import { readonly, ref, watch } from 'vue'
import { mapApiError } from '@/api/errors'
import { postIngest } from '@/api/ingest'
import { validateFile } from '@/lib/validators'
import type { UploadState } from '@/types/api'

export function useUpload() {
  const state = ref<UploadState>({ status: 'idle' })
  const elapsedSeconds = ref(0)
  const { pause, resume } = useIntervalFn(
    () => {
      elapsedSeconds.value += 1
    },
    1000,
    { immediate: false },
  )

  watch(
    () => state.value.status,
    (status) => {
      if (status === 'processing') {
        elapsedSeconds.value = 0
        resume()
        return
      }

      pause()
    },
  )

  function setDragging(isDragging: boolean) {
    state.value = isDragging ? { status: 'dragging' } : { status: 'idle' }
  }

  function reset() {
    state.value = { status: 'idle' }
  }

  function setError(message: string, code?: string) {
    state.value = code === undefined
      ? { status: 'error', message }
      : { status: 'error', message, code }
  }

  async function startUpload(file: File) {
    const validationError = validateFile(file)
    if (validationError !== null) {
      setError(validationError)
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
    elapsedSeconds: readonly(elapsedSeconds),
    startUpload,
    setDragging,
    setError,
    reset,
  }
}
