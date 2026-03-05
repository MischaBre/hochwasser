/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          900: 'var(--ink-900)',
          700: 'var(--ink-700)',
          500: 'var(--ink-500)',
        },
        surface: {
          100: 'var(--surface-100)',
          200: 'var(--surface-200)',
        },
        accent: {
          500: 'var(--accent-500)',
          600: 'var(--accent-600)',
        },
        alert: {
          500: 'var(--alert-500)',
        },
      },
      fontFamily: {
        body: ['var(--font-body)'],
        heading: ['var(--font-heading)'],
      },
      boxShadow: {
        soft: '0 14px 28px rgba(20, 53, 45, 0.1)',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: 0, transform: 'translateY(18px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in-up': 'fadeInUp 450ms ease-out both',
      },
    },
  },
  plugins: [],
}
