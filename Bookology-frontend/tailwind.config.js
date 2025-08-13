/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        off: '#e5e7eb',
        'off-90': '#f3f4f6',
        'off-70': '#d1d5db',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      backgroundImage: {
        'page-gradient': 'radial-gradient(1200px 800px at 20% 0%, #0A0F1F 0%, transparent 60%), radial-gradient(1400px 900px at 100% 0%, #0C0A1A 0%, #0C0A1A 60%)',
      },
      boxShadow: {
        'glow': '0 0 40px rgba(124,58,237,0.35)',
      },
      borderColor: {
        glass: 'rgba(255,255,255,0.12)',
      },
    },
  },
  plugins: [],
}