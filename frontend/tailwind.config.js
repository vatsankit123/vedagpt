/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: { colors: { saffron: {'500':'#f97c0e','600':'#ea6104','100':'#ffefd4','200':'#ffdba8','300':'#ffc070','400':'#ff9c36','700':'#c14807','800':'#99390d','900':'#7c300f','50':'#fff8ed'} } } },
  plugins: [],
}

