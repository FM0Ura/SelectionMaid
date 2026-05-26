<script setup lang="ts">
import { AlertCircle, RotateCcw } from 'lucide-vue-next'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

defineProps<{
  message: string
}>()

defineEmits<{
  retry: []
}>()
</script>

<template>
  <Alert class="border-destructive/40 bg-destructive/10 text-destructive">
    <div class="flex items-start gap-3">
      <AlertCircle class="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div class="min-w-0 flex-1">
        <p class="font-medium">Não foi possível enviar o arquivo</p>
        <p class="mt-1 text-sm text-destructive/90">{{ message }}</p>
      </div>
      <Button
        type="button"
        variant="destructive"
        size="sm"
        class="shrink-0"
        @click="$emit('retry')"
      >
        <RotateCcw aria-hidden="true" />
        Tentar novamente
      </Button>
    </div>
  </Alert>
</template>
