/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
          950: '#172554',
        },
        slate: {
          850: '#152033',
          900: '#0f172a',
          950: '#020617',
        },
        neon: {
          blue: '#38bdf8',
          cyan: '#22d3ee',
          purple: '#c084fc',
        }
      },
      backgroundImage: {
        'luxury-gradient': 'radial-gradient(circle at top, #0f172a 0%, #020617 100%)',
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.1)',
        'neon': '0 0 15px rgba(56, 189, 248, 0.3)',
        'neon-strong': '0 0 25px rgba(56, 189, 248, 0.5)',
      }
    },
  },
  plugins: [],
}
