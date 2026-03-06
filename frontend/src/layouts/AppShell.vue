<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import { computed } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { setAppLocale, supportedLocales, type SupportedLocale } from '@/plugins/i18n'

const { isAuthenticated, userEmail, signOut } = useAuth()
const route = useRoute()
const { locale, t } = useI18n()

const overviewActive = computed(() => route.path === '/')
const jobsActive = computed(() => route.path.startsWith('/jobs'))

const localeModel = computed({
  get: () => locale.value,
  set: (value: string) => {
    if (supportedLocales.includes(value as SupportedLocale)) {
      setAppLocale(value as SupportedLocale)
    }
  },
})

const navClass = (active: boolean): string => {
  return active
    ? 'rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-foreground'
    : 'rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground'
}
</script>

<template>
  <div class="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-6 md:px-8">
    <header class="mb-6 flex items-center justify-between rounded-lg border bg-card px-5 py-4">
      <div class="flex items-center gap-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{{ t('shell.appName') }}</p>
          <h1 class="text-xl font-semibold md:text-2xl">{{ t('shell.appSection') }}</h1>
        </div>
        <nav class="hidden items-center gap-2 md:flex">
          <RouterLink :class="navClass(overviewActive)" to="/">{{ t('shell.nav.overview') }}</RouterLink>
          <RouterLink :class="navClass(jobsActive)" to="/jobs">{{ t('shell.nav.jobs') }}</RouterLink>
        </nav>
      </div>
      <div class="flex items-center gap-3">
        <label class="sr-only" for="app-locale">{{ t('shell.locale.label') }}</label>
        <select
          id="app-locale"
          v-model="localeModel"
          class="h-8 rounded-md border border-input bg-background px-2 text-xs font-semibold uppercase tracking-wide"
        >
          <option v-for="nextLocale in supportedLocales" :key="nextLocale" :value="nextLocale">
            {{ t(`shell.locale.${nextLocale}`) }}
          </option>
        </select>
        <p v-if="isAuthenticated" class="hidden text-sm text-muted-foreground md:block">{{ userEmail }}</p>
        <Button
          v-if="isAuthenticated"
          variant="outline"
          size="sm"
          @click="signOut"
        >
          {{ t('shell.actions.signOut') }}
        </Button>
      </div>
    </header>

    <nav class="mb-4 flex items-center gap-2 md:hidden">
      <RouterLink :class="navClass(overviewActive)" to="/">{{ t('shell.nav.overview') }}</RouterLink>
      <RouterLink :class="navClass(jobsActive)" to="/jobs">{{ t('shell.nav.jobs') }}</RouterLink>
    </nav>

    <main>
      <RouterView />
    </main>
  </div>
</template>
