const requiredEnvVars = ['VITE_API_BASE_URL', 'VITE_SUPABASE_URL', 'VITE_SUPABASE_PUBLISHABLE_KEY'] as const

type RequiredEnvVar = (typeof requiredEnvVars)[number]

const readEnvVar = (key: RequiredEnvVar): string => {
  const value = import.meta.env[key]

  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`)
  }

  return value
}

export const env = {
  apiBaseUrl: readEnvVar('VITE_API_BASE_URL'),
  supabaseUrl: readEnvVar('VITE_SUPABASE_URL'),
  supabasePublishableKey: readEnvVar('VITE_SUPABASE_PUBLISHABLE_KEY'),
}
