/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#E8F5E9',
          100: '#C8E6C9',
          200: '#A5D6A7',
          500: '#4CAF50',
          600: '#43A047',
          700: '#388E3C',
          800: '#2E7D32',
          900: '#1B5E20',
        },
      },
    },
  },
  plugins: [],
  // Safelist dynamic classes used in ReportPage
  safelist: [
    'bg-brand-50', 'bg-orange-50', 'bg-blue-50',
    'text-brand-800', 'text-orange-700', 'text-blue-700',
  ],
};
