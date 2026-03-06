<script setup lang="ts">
const props = withDefaults(defineProps<{ modelValue: boolean; disabled?: boolean; inputId?: string }>(), {
  disabled: false,
  inputId: undefined,
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
}>()

const toggle = () => {
  if (props.disabled) {
    return
  }

  emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <button
    :id="inputId"
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :disabled="disabled"
    :data-state="modelValue ? 'checked' : 'unchecked'"
    class="peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-input"
    @click="toggle"
  >
    <span
      :data-state="modelValue ? 'checked' : 'unchecked'"
      class="pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0"
    />
  </button>
</template>
