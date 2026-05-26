<script setup lang="ts">
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
</script>

<template>
  <Card class="overflow-hidden bg-card/80 p-5">
    <div class="space-y-4">
      <Skeleton class="h-4 w-1/3 shimmer-gradient animate-shimmer" />
      <div class="space-y-2">
        <Skeleton class="h-3 w-full shimmer-gradient animate-shimmer" />
        <Skeleton class="h-3 w-11/12 shimmer-gradient animate-shimmer" />
        <Skeleton class="h-3 w-2/3 shimmer-gradient animate-shimmer" />
      </div>
    </div>
  </Card>
</template>
