<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ variant?: 'default' | 'destructive' }>(), {
  variant: 'default',
})

const variantClass = computed(() => {
  return props.variant === 'destructive'
    ? 'border-destructive/50 text-destructive [&>svg]:text-destructive'
    : 'text-foreground'
})
</script>

<template>
  <div
    role="alert"
    :class="[
      'relative w-full rounded-lg border p-4 text-sm [&_p]:leading-relaxed',
      variantClass,
    ]"
  >
    <slot />
  </div>
</template>
