type Translate = (key: string, params?: Record<string, unknown>) => string

type AuthErrorMessageOptions = {
  fallbackKey: string
  invalidCredentialsKey?: string
  passwordPolicyKey?: string
}

type ErrorLike = {
  message?: unknown
  code?: unknown
  status?: unknown
}

const getErrorLike = (error: unknown): ErrorLike => {
  if (error && typeof error === 'object') {
    return error as ErrorLike
  }

  return {}
}

const toLower = (value: unknown): string => {
  return typeof value === 'string' ? value.trim().toLowerCase() : ''
}

const includesAny = (value: string, tokens: string[]): boolean => {
  if (!value) {
    return false
  }

  return tokens.some((token) => value.includes(token))
}

export const toAuthErrorMessage = (
  error: unknown,
  t: Translate,
  options: AuthErrorMessageOptions,
): string => {
  const fallbackMessage = t(options.fallbackKey)
  const errorLike = getErrorLike(error)
  const message = toLower(errorLike.message)
  const code = toLower(errorLike.code)
  const status = typeof errorLike.status === 'number' ? errorLike.status : null

  if (
    status === 429 ||
    includesAny(code, ['over_request_rate_limit', 'over_email_send_rate_limit', 'too_many_requests']) ||
    includesAny(message, ['too many requests', 'rate limit'])
  ) {
    return t('auth.errors.rateLimited')
  }

  if (includesAny(message, ['failed to fetch', 'network error', 'network request failed'])) {
    return t('auth.errors.network')
  }

  if (
    includesAny(code, ['weak_password']) ||
    includesAny(message, ['password should', 'password must', 'weak password', 'password policy'])
  ) {
    return t(options.passwordPolicyKey ?? 'auth.errors.passwordPolicy')
  }

  if (includesAny(code, ['email_not_confirmed']) || includesAny(message, ['email not confirmed'])) {
    return t('auth.errors.emailNotConfirmed')
  }

  if (
    includesAny(code, ['invalid_credentials', 'invalid_grant']) ||
    includesAny(message, ['invalid login credentials', 'invalid credentials'])
  ) {
    return t(options.invalidCredentialsKey ?? 'auth.errors.invalidCredentials')
  }

  return fallbackMessage
}
