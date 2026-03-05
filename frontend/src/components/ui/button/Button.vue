<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
}>(), {
  variant: 'default',
  size: 'default',
  type: 'button',
  disabled: false,
})

const variantClass = computed(() => {
  switch (props.variant) {
    case 'secondary':
      return 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
    case 'outline':
      return 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'
    case 'ghost':
      return 'hover:bg-accent hover:text-accent-foreground'
    case 'destructive':
      return 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
    default:
      return 'bg-primary text-primary-foreground hover:bg-primary/90'
  }
})

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-9 rounded-md px-3'
    case 'lg':
      return 'h-11 rounded-md px-8'
    case 'icon':
      return 'h-10 w-10'
    default:
      return 'h-10 px-4 py-2'
  }
})
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    :class="[
      'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background disabled:pointer-events-none disabled:opacity-50',
      variantClass,
      sizeClass,
    ]"
  >
    <slot />
  </button>
</template>
