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
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const passwordVisible = ref(false)
const confirmPasswordVisible = ref(false)
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
    <Card>
      <CardHeader>
        <CardTitle>Create your account</CardTitle>
      </CardHeader>
      <CardContent>
        <form class="space-y-5" @submit.prevent="submit">
          <div class="space-y-2">
            <Label for="register-email">Email</Label>
            <Input id="register-email" v-model="email" autocomplete="email" type="email" required />
          </div>

          <div class="space-y-2">
            <Label for="register-password">Password</Label>
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
                :aria-label="passwordVisible ? 'Hide password' : 'Show password'"
                @click="passwordVisible = !passwordVisible"
              >
                <EyeOff v-if="passwordVisible" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </div>
          </div>

          <div class="space-y-2">
            <Label for="register-password-confirm">Confirm password</Label>
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
                :aria-label="confirmPasswordVisible ? 'Hide confirm password' : 'Show confirm password'"
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
            {{ authStore.loading ? 'Creating account...' : 'Create account' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter>
        <Button variant="outline" @click="goLogin">Back to login</Button>
      </CardFooter>
    </Card>
  </section>
</template>
