<script setup lang="ts">
import { Eye, EyeOff } from 'lucide-vue-next'
import Alert from '@/components/ui/alert/Alert.vue'
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardFooter from '@/components/ui/card/CardFooter.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import Input from '@/components/ui/input/Input.vue'
import Label from '@/components/ui/label/Label.vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { toAuthErrorMessage } from '@/features/auth/errorMessages'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const passwordVisible = ref(false)
const confirmPasswordVisible = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const rateLimitStorageKey = 'register.attempts'
const rateLimitWindowMs = 15 * 60 * 1000
const rateLimitMaxAttempts = 5

const getRecentRegisterAttempts = (): number[] => {
  const raw = localStorage.getItem(rateLimitStorageKey)
  if (!raw) {
    return []
  }

  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      return []
    }

    const now = Date.now()
    return parsed
      .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
      .filter((timestamp) => now - timestamp <= rateLimitWindowMs)
  } catch {
    return []
  }
}

const trackRegisterAttempt = () => {
  const nextAttempts = [...getRecentRegisterAttempts(), Date.now()]
  localStorage.setItem(rateLimitStorageKey, JSON.stringify(nextAttempts))
}

const goLogin = () => {
  router.push('/login')
}

const submit = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (password.value !== confirmPassword.value) {
    errorMessage.value = t('auth.register.passwordsMismatch')
    return
  }

  const recentAttempts = getRecentRegisterAttempts()
  if (recentAttempts.length >= rateLimitMaxAttempts) {
    errorMessage.value = t('auth.register.rateLimited', { minutes: 15 })
    return
  }

  trackRegisterAttempt()

  try {
    await authStore.signUp(email.value.trim(), password.value)
    successMessage.value = t('auth.register.createdCheckInbox')
  } catch (error) {
    errorMessage.value = toAuthErrorMessage(error, t, {
      fallbackKey: 'auth.register.failedFallback',
      passwordPolicyKey: 'auth.register.passwordPolicy',
    })
  }
}
</script>

<template>
  <section class="mx-auto max-w-lg">
    <Card>
      <CardHeader>
        <CardTitle>{{ t('auth.register.title') }}</CardTitle>
      </CardHeader>
      <CardContent>
        <form class="space-y-5" @submit.prevent="submit">
          <div class="space-y-2">
            <Label for="register-email">{{ t('auth.register.email') }}</Label>
            <Input id="register-email" v-model="email" autocomplete="email" type="email" required />
          </div>

          <div class="space-y-2">
            <Label for="register-password">{{ t('auth.register.password') }}</Label>
            <div class="relative">
              <Input
                id="register-password"
                v-model="password"
                autocomplete="new-password"
                :type="passwordVisible ? 'text' : 'password'"
                class="pr-11"
                required
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 inline-flex w-10 items-center justify-center text-muted-foreground hover:text-foreground"
                :aria-label="passwordVisible ? t('auth.register.hidePassword') : t('auth.register.showPassword')"
                @click="passwordVisible = !passwordVisible"
              >
                <EyeOff v-if="passwordVisible" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </div>
          </div>

          <div class="space-y-2">
            <Label for="register-password-confirm">{{ t('auth.register.confirmPassword') }}</Label>
            <div class="relative">
              <Input
                id="register-password-confirm"
                v-model="confirmPassword"
                autocomplete="new-password"
                :type="confirmPasswordVisible ? 'text' : 'password'"
                class="pr-11"
                required
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 inline-flex w-10 items-center justify-center text-muted-foreground hover:text-foreground"
                :aria-label="confirmPasswordVisible ? t('auth.register.hideConfirmPassword') : t('auth.register.showConfirmPassword')"
                @click="confirmPasswordVisible = !confirmPasswordVisible"
              >
                <EyeOff v-if="confirmPasswordVisible" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </div>
          </div>

          <Alert v-if="successMessage">{{ successMessage }}</Alert>
          <Alert v-if="errorMessage" variant="destructive">{{ errorMessage }}</Alert>

          <Button class="w-full" type="submit" :disabled="authStore.loading">
            {{ authStore.loading ? t('auth.register.submitting') : t('auth.register.submit') }}
          </Button>
        </form>
      </CardContent>
      <CardFooter>
        <Button variant="outline" @click="goLogin">{{ t('auth.register.backToLogin') }}</Button>
      </CardFooter>
    </Card>
  </section>
</template>
