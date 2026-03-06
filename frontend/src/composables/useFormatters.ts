import { DateTime } from 'luxon'
import { useI18n } from 'vue-i18n'

type NumberFormatOptions = Intl.NumberFormatOptions

export const useFormatters = () => {
  const { locale } = useI18n()

  const formatNumber = (value: number, options?: NumberFormatOptions): string => {
    return new Intl.NumberFormat(locale.value, options).format(value)
  }

  const formatDateTime = (value: string): string => {
    const dateTime = DateTime.fromISO(value, { setZone: true })

    if (!dateTime.isValid) {
      return value
    }

    return dateTime.setLocale(locale.value).toLocaleString(DateTime.DATETIME_MED)
  }

  const formatRelativeDateTime = (value: string): string | null => {
    const dateTime = DateTime.fromISO(value, { setZone: true })

    if (!dateTime.isValid) {
      return null
    }

    return dateTime.setLocale(locale.value).toRelative()
  }

  return {
    formatDateTime,
    formatRelativeDateTime,
    formatNumber,
  }
}
