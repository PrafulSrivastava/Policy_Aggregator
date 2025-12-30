/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Swiss Palette
        black: '#000000',
        white: '#FFFFFF',
        primary: '#000000', // Black is the primary structural color
        accent: '#FF3000',  // Swiss Red for signals
        muted: '#F2F2F2',   // Light gray for rhythm
        
        // Semantic mapping
        success: '#000000', // Success is just objective fact in Swiss style
        warning: '#FF3000', // Warnings are red
        error: '#FF3000',   // Errors are red
        
        slate: {
          50: '#F2F2F2',    // Muted
          100: '#E5E5E5',
          200: '#CCCCCC',
          300: '#B3B3B3',
          400: '#999999',
          500: '#808080',
          600: '#666666',
          700: '#4D4D4D',
          800: '#333333',
          900: '#1A1A1A',
          950: '#000000',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"SF Mono"', '"Monaco"', '"Courier New"', 'monospace'],
      },
      borderWidth: {
        DEFAULT: '1px',
        '0': '0',
        '2': '2px',
        '3': '3px',
        '4': '4px',
      },
      letterSpacing: {
        tighter: '-0.05em',
        tight: '-0.025em',
        normal: '0em',
        wide: '0.025em',
        wider: '0.05em',
        widest: '0.1em',
      },
      backgroundImage: {
        'swiss-grid': `
          linear-gradient(to right, rgba(0,0,0,0.05) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(0,0,0,0.05) 1px, transparent 1px)
        `,
        'swiss-dots': 'radial-gradient(rgba(0,0,0,0.15) 1px, transparent 1px)',
      },
      backgroundSize: {
        'swiss-grid': '24px 24px',
        'swiss-dots': '16px 16px',
      },
    },
  },
  plugins: [],
}

