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
  safelist: [
    // ReportPage dynamic classes
    'bg-brand-50', 'bg-orange-50', 'bg-blue-50',
    'text-brand-800', 'text-orange-700', 'text-blue-700',
    // Deal Radar ScoreBadge
    'bg-red-100', 'text-red-700', 'border-red-200',
    'bg-yellow-100', 'text-yellow-700', 'border-yellow-200',
    'bg-green-100', 'text-green-700', 'border-green-200',
    'bg-gray-100', 'text-gray-500', 'border-gray-200',
    // WatchlistPanel stage chips
    'bg-purple-50', 'text-purple-700',
    'bg-blue-50', 'text-blue-700',
    'bg-cyan-50', 'text-cyan-700',
    'bg-teal-50', 'text-teal-700',
  ],
};
