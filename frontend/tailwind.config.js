/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        dusk: {
          950: '#12132A', // deepest background
          900: '#17182F', // page background
          800: '#1F2140', // raised surface
          700: '#2A2C52', // card border / hover surface
          600: '#3A3D6B',
        },
        lamp: {
          400: '#F0BC7A',
          500: '#E8A854', // primary accent — warm lamplight
          600: '#C98A38',
        },
        sage: {
          400: '#8FC49B',
          500: '#7FB68B', // calm/positive accent, used sparingly (mood UI)
        },
        ink: {
          100: '#F5F1E8', // primary text on dark
          300: '#C9C7DA',
          400: '#A8A9C4', // muted/secondary text
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      keyframes: {
        breathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.55' },
          '50%': { transform: 'scale(1.08)', opacity: '0.85' },
        },
      },
      animation: {
        breathe: 'breathe 6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
