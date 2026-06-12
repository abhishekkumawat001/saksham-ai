/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#FEFCE8',
        ink: '#1C1917',
        brand: '#1B6B3A',
      },
    },
  },
  plugins: [],
};
