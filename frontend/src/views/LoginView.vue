<script setup lang="ts">
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
    <Card>
      <CardHeader>
        <CardTitle>Welcome back</CardTitle>
      </CardHeader>
      <CardContent>
        <form class="space-y-5" @submit.prevent="submit">
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input id="email" v-model="email" autocomplete="email" type="email" required />
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input id="password" v-model="password" autocomplete="current-password" type="password" required />
          </div>

          <Alert v-if="errorMessage" variant="destructive">{{ errorMessage }}</Alert>

          <Button class="w-full" type="submit" :disabled="authStore.loading">
            {{ authStore.loading ? 'Signing in...' : 'Sign in' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter>
        <div class="mt-1 text-sm text-muted-foreground">
          New here?
          <RouterLink class="font-semibold text-primary hover:underline" to="/register">Create account</RouterLink>
        </div>
      </CardFooter>
    </Card>
  </section>
</template>
