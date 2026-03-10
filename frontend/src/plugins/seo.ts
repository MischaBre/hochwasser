import { watch } from 'vue'
import type { Router, RouteLocationNormalizedLoaded } from 'vue-router'
import { i18n } from '@/plugins/i18n'

const siteName = 'Pegel-Alarm'
const defaultImagePath = '/favicon-32.png'

type SeoConfig = {
  title: string
  description: string
  noindex?: boolean
}

const routeSeoConfig = (route: RouteLocationNormalizedLoaded): SeoConfig => {
  const { t } = i18n.global
  const noindex = Boolean(route.meta.requiresAuth || route.meta.noindex)

  const byName: Record<string, SeoConfig> = {
    landing: {
      title: t('seo.routes.landing.title'),
      description: t('seo.routes.landing.description'),
    },
    login: {
      title: t('seo.routes.login.title'),
      description: t('seo.routes.login.description'),
      noindex: true,
    },
    register: {
      title: t('seo.routes.register.title'),
      description: t('seo.routes.register.description'),
      noindex: true,
    },
    impressum: {
      title: t('seo.routes.imprint.title'),
      description: t('seo.routes.imprint.description'),
    },
    privacy: {
      title: t('seo.routes.privacy.title'),
      description: t('seo.routes.privacy.description'),
    },
    'not-found': {
      title: t('seo.routes.notFound.title'),
      description: t('seo.routes.notFound.description'),
      noindex: true,
    },
  }

  return byName[String(route.name)] ?? {
    title: `${siteName} App`,
    description: t('seo.routes.app.description'),
    noindex,
  }
}

const upsertMetaTag = (
  key: 'name' | 'property',
  value: string,
  content: string,
): void => {
  let element = document.head.querySelector<HTMLMetaElement>(`meta[${key}="${value}"]`)

  if (!element) {
    element = document.createElement('meta')
    element.setAttribute(key, value)
    document.head.appendChild(element)
  }

  element.setAttribute('content', content)
}

const upsertLinkTag = (rel: string, href: string): void => {
  let element = document.head.querySelector<HTMLLinkElement>(`link[rel="${rel}"]`)

  if (!element) {
    element = document.createElement('link')
    element.setAttribute('rel', rel)
    document.head.appendChild(element)
  }

  element.setAttribute('href', href)
}

const removeMetaTag = (key: 'name' | 'property', value: string): void => {
  document.head.querySelector(`meta[${key}="${value}"]`)?.remove()
}

const upsertJsonLd = (route: RouteLocationNormalizedLoaded): void => {
  const scriptId = 'seo-jsonld'
  const existing = document.getElementById(scriptId)
  const shouldInclude = route.name === 'landing'

  if (!shouldInclude) {
    existing?.remove()
    return
  }

  const origin = window.location.origin
  const payload = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: siteName,
    applicationCategory: 'UtilitiesApplication',
    operatingSystem: 'Web',
    url: new URL(route.fullPath, origin).toString(),
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'EUR',
    },
    inLanguage: i18n.global.locale.value,
  }

  const script = existing ?? document.createElement('script')
  script.id = scriptId
  script.setAttribute('type', 'application/ld+json')
  script.textContent = JSON.stringify(payload)

  if (!existing) {
    document.head.appendChild(script)
  }
}

const applySeo = (route: RouteLocationNormalizedLoaded): void => {
  const config = routeSeoConfig(route)
  const title = config.title.includes(siteName) ? config.title : `${config.title} | ${siteName}`
  const canonical = new URL(route.fullPath, window.location.origin).toString()
  const image = new URL(defaultImagePath, window.location.origin).toString()

  document.title = title

  upsertMetaTag('name', 'description', config.description)
  upsertMetaTag('property', 'og:type', 'website')
  upsertMetaTag('property', 'og:site_name', siteName)
  upsertMetaTag('property', 'og:title', title)
  upsertMetaTag('property', 'og:description', config.description)
  upsertMetaTag('property', 'og:url', canonical)
  upsertMetaTag('property', 'og:image', image)
  upsertMetaTag('name', 'twitter:card', 'summary')
  upsertMetaTag('name', 'twitter:title', title)
  upsertMetaTag('name', 'twitter:description', config.description)
  upsertMetaTag('name', 'twitter:image', image)
  upsertMetaTag('name', 'robots', config.noindex ? 'noindex, nofollow' : 'index, follow')
  upsertLinkTag('canonical', canonical)

  if (!config.noindex) {
    removeMetaTag('name', 'googlebot')
  }

  upsertJsonLd(route)
}

export const initSeo = (router: Router): void => {
  watch(
    () => i18n.global.locale.value,
    () => {
      applySeo(router.currentRoute.value)
    },
  )

  router.afterEach((to) => {
    applySeo(to)
  })

  applySeo(router.currentRoute.value)
}
