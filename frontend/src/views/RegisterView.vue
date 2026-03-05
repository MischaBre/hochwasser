<script setup lang="ts">
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const successMessage = ref('')

const goLogin = () => {
  router.push('/login')
}

const submit = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  try {
    const data = await authStore.signUp(email.value.trim(), password.value)

    if (data.session) {
      await router.push('/')
      return
    }

    successMessage.value = 'Account created. Check your inbox to confirm your email, then sign in.'
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Registration failed. Please try again.'
    errorMessage.value = message
  }
}
</script>

<template>
  <section class="mx-auto max-w-lg">
    <Card class="glass-card rounded-2xl">
      <template #title>
        <h2 class="text-2xl font-semibold text-ink-900">Create your account</h2>
      </template>
      <template #content>
        <form class="space-y-4" @submit.prevent="submit">
          <span class="p-float-label block">
            <InputText id="register-email" v-model="email" class="w-full" autocomplete="email" type="email" required />
            <label for="register-email">Email</label>
          </span>

          <span class="p-float-label block">
            <Password
              id="register-password"
              v-model="password"
              class="w-full"
              input-class="w-full"
              autocomplete="new-password"
              toggle-mask
              required
            />
            <label for="register-password">Password</label>
          </span>

          <span class="p-float-label block">
            <Password
              id="register-password-confirm"
              v-model="confirmPassword"
              class="w-full"
              input-class="w-full"
              :feedback="false"
              autocomplete="new-password"
              toggle-mask
              required
            />
            <label for="register-password-confirm">Confirm password</label>
          </span>

          <Message v-if="successMessage" severity="success" :closable="false">{{ successMessage }}</Message>
          <Message v-if="errorMessage" severity="error" :closable="false">{{ errorMessage }}</Message>

          <Button class="w-full" type="submit" label="Create account" icon="pi pi-user-plus" :loading="authStore.loading" />
        </form>
      </template>
      <template #footer>
        <Button label="Back to login" icon="pi pi-arrow-left" outlined @click="goLogin" />
      </template>
    </Card>
  </section>
</template>
