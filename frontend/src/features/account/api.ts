import { apiRequest } from '@/api/client'

export type MeResponse = {
  user_id: string
  org_id: string
  role: 'admin' | 'member'
  active_jobs_count: number
  max_active_jobs: number
  max_alarm_recipients_per_job: number
}

export const getMe = () => apiRequest<MeResponse>('/v1/me')

export const deleteMe = () => apiRequest<void>('/v1/me', { method: 'DELETE' })
