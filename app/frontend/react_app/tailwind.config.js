/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'],
        display: ['Manrope', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace']
      },
      colors: {
        clinical: {
          navy: '#0B1B33',
          navyDeep: '#071224',
          blue: '#2563EB',
          model: '#0D9488',
          modelDeep: '#0F766E',
          surface: '#F4F6FA',
          card: '#FFFFFF',
          border: '#E2E8F0',
          ink: '#0B1220',
          muted: '#5B6B85'
        },
        acuity: {
          1: '#7F1D1D',
          2: '#DC2626',
          3: '#D97706',
          4: '#2563EB',
          5: '#16A34A'
        }
      },
      boxShadow: {
        soft: '0 18px 45px rgba(11, 27, 51, 0.10)',
        card: '0 10px 28px rgba(11, 27, 51, 0.06)',
        pop: '0 24px 60px rgba(11, 27, 51, 0.16)'
      },
      keyframes: {
        'toast-in': {
          '0%': { opacity: '0', transform: 'translateY(8px) scale(0.98)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-480px 0' },
          '100%': { backgroundPosition: '480px 0' }
        }
      },
      animation: {
        'toast-in': 'toast-in 0.22s ease-out',
        shimmer: 'shimmer 1.6s ease-in-out infinite'
      }
    }
  },
  plugins: []
};
