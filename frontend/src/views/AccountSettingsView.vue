<script setup lang="ts">
import { ref } from 'vue'
import { useMutation } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Alert from '@/components/ui/alert/Alert.vue'
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import Input from '@/components/ui/input/Input.vue'
import Label from '@/components/ui/label/Label.vue'
import { deleteMe } from '@/features/account/api'
import { useCurrentUserQuery } from '@/features/account/useCurrentUser'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const currentUserQuery = useCurrentUserQuery()

const currentPassword = ref('')
const newPassword = ref('')
const confirmNewPassword = ref('')
const changePasswordError = ref('')
const changePasswordSuccess = ref('')

const deleteConfirmation = ref('')

const deleteMutation = useMutation({
  mutationFn: deleteMe,
  onSuccess: async () => {
    await authStore.signOut()
    await router.push('/')
  },
})

const submitPasswordChange = async () => {
  changePasswordError.value = ''
  changePasswordSuccess.value = ''

  if (newPassword.value !== confirmNewPassword.value) {
    changePasswordError.value = t('account.password.errors.mismatch')
    return
  }

  if (newPassword.value.length < 8) {
    changePasswordError.value = t('account.password.errors.minLength')
    return
  }

  try {
    await authStore.changePassword(currentPassword.value, newPassword.value)
    currentPassword.value = ''
    newPassword.value = ''
    confirmNewPassword.value = ''
    changePasswordSuccess.value = t('account.password.success')
  } catch (error) {
    changePasswordError.value = error instanceof Error ? error.message : t('account.password.errors.failed')
  }
}

const submitAccountDelete = async () => {
  if (deleteConfirmation.value.trim() !== 'DELETE') {
    return
  }
  await deleteMutation.mutateAsync()
}
</script>

<template>
  <section class="space-y-4">
    <Card>
      <CardHeader>
        <CardTitle>{{ t('account.title') }}</CardTitle>
      </CardHeader>
      <CardContent>
        <p class="text-sm text-muted-foreground">
          {{ t('account.subtitle') }}
        </p>
        <div v-if="currentUserQuery.data.value" class="mt-4 rounded-md border bg-muted/20 p-3 text-sm">
          <p>
            {{ t('account.limits.activeJobs', {
              current: currentUserQuery.data.value.active_jobs_count,
              max: currentUserQuery.data.value.max_active_jobs,
            }) }}
          </p>
          <p class="mt-1 text-muted-foreground">
            {{ t('account.limits.maxRecipients', { max: currentUserQuery.data.value.max_alarm_recipients_per_job }) }}
          </p>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>{{ t('account.password.title') }}</CardTitle>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="submitPasswordChange">
          <div class="space-y-2">
            <Label for="current-password">{{ t('account.password.current') }}</Label>
            <Input id="current-password" v-model="currentPassword" type="password" autocomplete="current-password" required />
          </div>
          <div class="space-y-2">
            <Label for="new-password">{{ t('account.password.new') }}</Label>
            <Input id="new-password" v-model="newPassword" type="password" autocomplete="new-password" required />
          </div>
          <div class="space-y-2">
            <Label for="confirm-new-password">{{ t('account.password.confirm') }}</Label>
            <Input id="confirm-new-password" v-model="confirmNewPassword" type="password" autocomplete="new-password" required />
          </div>

          <Alert v-if="changePasswordSuccess">{{ changePasswordSuccess }}</Alert>
          <Alert v-if="changePasswordError" variant="destructive">{{ changePasswordError }}</Alert>

          <Button type="submit" :disabled="authStore.loading">{{ t('account.password.submit') }}</Button>
        </form>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>{{ t('account.delete.title') }}</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <Alert variant="destructive">{{ t('account.delete.warning') }}</Alert>
        <p class="text-sm text-muted-foreground">{{ t('account.delete.instructions') }}</p>
        <div class="space-y-2">
          <Label for="delete-confirmation">{{ t('account.delete.confirmLabel') }}</Label>
          <Input id="delete-confirmation" v-model="deleteConfirmation" />
        </div>
        <Button
          variant="destructive"
          :disabled="deleteMutation.isPending.value || deleteConfirmation.trim() !== 'DELETE'"
          @click="submitAccountDelete"
        >
          {{ t('account.delete.submit') }}
        </Button>
        <Alert v-if="deleteMutation.isError.value" variant="destructive">
          {{ deleteMutation.error.value instanceof Error ? deleteMutation.error.value.message : t('account.delete.failed') }}
        </Alert>
      </CardContent>
    </Card>
  </section>
</template>
