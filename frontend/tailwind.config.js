/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FFFFFF',
        foreground: '#000000',
        muted: '#F5F5F5',
        mutedForeground: '#525252',
        accent: '#000000',
        accentForeground: '#FFFFFF',
        border: '#000000',
        borderLight: '#E5E5E5',
        card: '#FFFFFF',
        cardForeground: '#000000',
        ring: '#000000',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        body: ['"Source Serif 4"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '0px',
      },
      transitionDuration: {
        'instant': '100ms',
      },
    },
  },
  plugins: [],
}

