<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <section class="mx-auto mt-14 max-w-xl rounded-lg border bg-card p-8 text-center text-card-foreground">
    <p class="mb-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">404</p>
    <h2 class="mb-2 text-3xl font-semibold">{{ t('notFound.title') }}</h2>
    <p class="text-sm text-muted-foreground">{{ t('notFound.description') }}</p>
    <RouterLink class="mt-5 inline-block text-sm font-semibold text-primary hover:underline" to="/">
      {{ t('notFound.action') }}
    </RouterLink>
  </section>
</template>
