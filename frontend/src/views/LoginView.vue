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
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()

const email = ref('')
const password = ref('')
const passwordVisible = ref(false)
const errorMessage = ref('')

const redirectPath = computed(() => (route.query.redirect as string) || '/')

const submit = async () => {
  errorMessage.value = ''

  try {
    await authStore.signIn(email.value.trim(), password.value)
    await router.push(redirectPath.value)
  } catch (error) {
    const message = error instanceof Error ? error.message : t('auth.login.failedFallback')
    errorMessage.value = message
  }
}
</script>

<template>
  <section class="mx-auto max-w-lg">
    <Card>
      <CardHeader>
        <CardTitle>{{ t('auth.login.title') }}</CardTitle>
      </CardHeader>
      <CardContent>
        <form class="space-y-5" @submit.prevent="submit">
          <div class="space-y-2">
            <Label for="email">{{ t('auth.login.email') }}</Label>
            <Input id="email" v-model="email" autocomplete="email" type="email" required />
          </div>

          <div class="space-y-2">
            <Label for="password">{{ t('auth.login.password') }}</Label>
            <div class="relative">
              <Input
                id="password"
                v-model="password"
                autocomplete="current-password"
                :type="passwordVisible ? 'text' : 'password'"
                class="pr-11"
                required
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 inline-flex w-10 items-center justify-center text-muted-foreground hover:text-foreground"
                :aria-label="passwordVisible ? t('auth.login.hidePassword') : t('auth.login.showPassword')"
                @click="passwordVisible = !passwordVisible"
              >
                <EyeOff v-if="passwordVisible" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </div>
          </div>

          <Alert v-if="errorMessage" variant="destructive">{{ errorMessage }}</Alert>

          <Button class="w-full" type="submit" :disabled="authStore.loading">
            {{ authStore.loading ? t('auth.login.submitting') : t('auth.login.submit') }}
          </Button>
        </form>
      </CardContent>
      <CardFooter>
        <div class="mt-1 text-sm text-muted-foreground">
          {{ t('auth.login.newHere') }}
          <RouterLink class="font-semibold text-primary hover:underline" to="/register">{{ t('auth.login.createAccount') }}</RouterLink>
        </div>
      </CardFooter>
    </Card>
  </section>
</template>
