/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0F19',
        surface: '#1A1F2C',
        primary: '#7C3AED', // Purple
        primaryHover: '#6D28D9',
        textPrimary: '#F8FAFC',
        textSecondary: '#94A3B8',
        border: '#2E364F'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
