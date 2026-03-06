import { apiRequest } from '@/api/client'

export type MeResponse = {
  user_id: string
  org_id: string
  role: 'admin' | 'member'
}

export const getMe = () => apiRequest<MeResponse>('/v1/me')
