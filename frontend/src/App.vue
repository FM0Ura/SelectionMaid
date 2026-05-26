<script setup lang="ts">
import DropZone from '@/components/upload/DropZone.vue'
</script>

<template>
  <main class="flex min-h-screen flex-col items-center justify-center gap-8 bg-background px-6 py-10 text-foreground">
    <section class="w-full max-w-2xl space-y-3 text-center">
      <p class="text-sm font-medium text-muted-foreground">SelectionMaid</p>
      <h1 class="text-3xl font-semibold leading-tight">Transforme documentos em chunks Markdown</h1>
    </section>
    <DropZone />
  </main>
</template>
