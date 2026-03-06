import { createI18n } from 'vue-i18n'
import de from '@/locales/de'
import en from '@/locales/en'

export const supportedLocales = ['de', 'en'] as const
export type SupportedLocale = typeof supportedLocales[number]

const fallbackLocale: SupportedLocale = 'de'
const localeStorageKey = 'hochwasser.locale'

const isSupportedLocale = (value: string): value is SupportedLocale => {
  return supportedLocales.includes(value as SupportedLocale)
}

const normalizeLocale = (value: string): SupportedLocale | null => {
  const lowered = value.trim().toLowerCase()

  if (!lowered) {
    return null
  }

  if (isSupportedLocale(lowered)) {
    return lowered
  }

  const [language] = lowered.split('-')
  if (language && isSupportedLocale(language)) {
    return language
  }

  return null
}

const getStoredLocale = (): SupportedLocale | null => {
  if (typeof window === 'undefined') {
    return null
  }

  const stored = window.localStorage.getItem(localeStorageKey)
  return stored ? normalizeLocale(stored) : null
}

const getBrowserLocale = (): SupportedLocale | null => {
  if (typeof window === 'undefined') {
    return null
  }

  for (const locale of window.navigator.languages) {
    const normalized = normalizeLocale(locale)
    if (normalized) {
      return normalized
    }
  }

  return normalizeLocale(window.navigator.language)
}

const resolveInitialLocale = (): SupportedLocale => {
  return getStoredLocale() ?? getBrowserLocale() ?? fallbackLocale
}

const messages = {
  de,
  en,
}

export const i18n = createI18n({
  legacy: false,
  locale: resolveInitialLocale(),
  fallbackLocale,
  messages,
})

const updateHtmlLanguage = (locale: SupportedLocale): void => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale
  }
}

export const setAppLocale = (locale: SupportedLocale): void => {
  i18n.global.locale.value = locale
  updateHtmlLanguage(locale)

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(localeStorageKey, locale)
  }
}

export const initializeAppLocale = (): void => {
  updateHtmlLanguage(i18n.global.locale.value as SupportedLocale)
}
