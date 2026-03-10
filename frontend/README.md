# Hochwasser Frontend

Vue 3 + TypeScript frontend for auth and job management.

## Setup

1. Copy `.env.example` to `.env`
2. Set your Supabase, API, and site URL values (`VITE_*`)
3. Install dependencies

```bash
npm install
```

## Development

Run standalone frontend dev server:

```bash
npm run dev
```

Default URL: `http://localhost:5173`

If you run the full stack via Docker Compose from repo root, use root `.env` for `VITE_*` values.

```bash
make up-dev
```

## Build

```bash
npm run build
```

`npm run build` automatically generates `public/robots.txt` and `public/sitemap.xml`.
Set `VITE_SITE_URL` to your production domain so canonical URLs and sitemap entries are correct.
