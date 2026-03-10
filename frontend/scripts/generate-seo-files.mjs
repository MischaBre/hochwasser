import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'

const siteUrl = (process.env.VITE_SITE_URL || process.env.SITE_URL || 'http://localhost:5173').replace(
  /\/$/,
  '',
)

const publicRoutes = ['/', '/impressum', '/datenschutz']
const lastmod = new Date().toISOString().slice(0, 10)

const toAbsoluteUrl = (path) => `${siteUrl}${path}`

const robotsContent = `User-agent: *
Allow: /

Sitemap: ${toAbsoluteUrl('/sitemap.xml')}
`

const sitemapContent = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${publicRoutes
  .map(
    (path) => `  <url>
    <loc>${toAbsoluteUrl(path)}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${path === '/' ? 'daily' : 'monthly'}</changefreq>
    <priority>${path === '/' ? '1.0' : '0.5'}</priority>
  </url>`,
  )
  .join('\n')}
</urlset>
`

const robotsPath = resolve('public/robots.txt')
const sitemapPath = resolve('public/sitemap.xml')

await mkdir(dirname(robotsPath), { recursive: true })
await writeFile(robotsPath, robotsContent, 'utf8')
await writeFile(sitemapPath, sitemapContent, 'utf8')

console.log(`Generated robots.txt and sitemap.xml for ${siteUrl}`)
