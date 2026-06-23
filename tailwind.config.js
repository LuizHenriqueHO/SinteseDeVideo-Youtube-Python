/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./templates/**/*.html'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        tubify: {
          green: '#16A34A',
          light: '#86EFAC',
          dark: '#14532D',
          bg: '#F3F4F6',
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
