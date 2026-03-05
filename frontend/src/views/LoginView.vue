<script setup lang="ts">
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const errorMessage = ref('')

const redirectPath = computed(() => (route.query.redirect as string) || '/')

const submit = async () => {
  errorMessage.value = ''

  try {
    await authStore.signIn(email.value.trim(), password.value)
    await router.push(redirectPath.value)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Login failed. Please try again.'
    errorMessage.value = message
  }
}
</script>

<template>
  <section class="mx-auto max-w-lg">
    <Card class="glass-card rounded-2xl">
      <template #title>
        <h2 class="text-2xl font-semibold text-ink-900">Welcome back</h2>
      </template>
      <template #content>
        <form class="space-y-4" @submit.prevent="submit">
          <span class="p-float-label block">
            <InputText id="email" v-model="email" class="w-full" autocomplete="email" type="email" required />
            <label for="email">Email</label>
          </span>

          <span class="p-float-label block">
            <Password
              id="password"
              v-model="password"
              class="w-full"
              input-class="w-full"
              :feedback="false"
              autocomplete="current-password"
              toggle-mask
              required
            />
            <label for="password">Password</label>
          </span>

          <Message v-if="errorMessage" severity="error" :closable="false">{{ errorMessage }}</Message>

          <Button class="w-full" type="submit" label="Sign in" icon="pi pi-sign-in" :loading="authStore.loading" />
        </form>
      </template>
      <template #footer>
        <div class="mt-3 text-sm text-ink-700">
          New here?
          <RouterLink class="font-semibold text-accent-600 hover:text-accent-500" to="/register">Create account</RouterLink>
        </div>
      </template>
    </Card>
  </section>
</template>
