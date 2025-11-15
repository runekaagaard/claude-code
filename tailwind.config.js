/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./build/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        'claude-orange': '#D97757',
      }
    }
  },
  plugins: [],
}
