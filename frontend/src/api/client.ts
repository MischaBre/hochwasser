import { env } from '@/lib/env'
import { i18n } from '@/plugins/i18n'
import { useAuthStore } from '@/stores/auth'

type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE'

type RequestConfig = {
  method?: HttpMethod
  body?: unknown
  headers?: Record<string, string>
}

export type ValidationIssue = {
  loc?: Array<string | number>
  msg?: string
  type?: string
}

type ApiErrorPayload = {
  detail?: string | ValidationIssue[]
}

export class ApiError extends Error {
  status: number
  validationIssues: ValidationIssue[]

  constructor(status: number, message: string, validationIssues: ValidationIssue[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.validationIssues = validationIssues
  }
}

const parseErrorPayload = async (response: Response): Promise<ApiErrorPayload> => {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    return (await response.json()) as ApiErrorPayload
  }

  const text = await response.text()
  return { detail: text || undefined }
}

const getErrorMessage = (status: number, payload: ApiErrorPayload): string => {
  if (Array.isArray(payload.detail)) {
    return i18n.global.t('api.validationFailed')
  }

  if (typeof payload.detail === 'string' && payload.detail.length > 0) {
    return payload.detail
  }

  if (status === 401) {
    return i18n.global.t('api.authRequired')
  }

  if (status === 403) {
    return i18n.global.t('api.actionNotAllowed')
  }

  return i18n.global.t('api.requestFailedStatus', { status })
}

const handleHttpError = async (response: Response): Promise<never> => {
  const authStore = useAuthStore()
  const payload = await parseErrorPayload(response)
  const message = getErrorMessage(response.status, payload)
  const validationIssues = Array.isArray(payload.detail) ? payload.detail : []

  if (response.status === 401 && authStore.isAuthenticated) {
    await authStore.signOut()
  }

  throw new ApiError(response.status, message, validationIssues)
}

export const apiRequest = async <T>(path: string, config: RequestConfig = {}): Promise<T> => {
  const authStore = useAuthStore()
  const token = authStore.getAccessToken()
  const hasBody = config.body !== undefined

  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    method: config.method ?? 'GET',
    headers: {
      ...(hasBody ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...config.headers,
    },
    body: hasBody ? JSON.stringify(config.body) : undefined,
  })

  if (!response.ok) {
    await handleHttpError(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    return (await response.text()) as T
  }

  return (await response.json()) as T
}
