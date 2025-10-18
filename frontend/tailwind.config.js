/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Chat page colors
        "primary": "#2D9A86",
        "background-light": "#f6f8f8",
        "background-dark": "#11211e",
        "assistant-bubble-light": "#e8f3f1",
        "assistant-bubble-dark": "#1f3a35",
        "assistant-text-light": "#0e1b18",
        "assistant-text-dark": "#ffffff",
        "user-bubble-light": "#ffffff",
        "user-bubble-dark": "#2d9a86",
        "user-text-light": "#0e1b18",
        "user-text-dark": "#ffffff",
        "input-bg-light": "#e8f3f1",
        "input-bg-dark": "#1f3a35",
        "input-text-light": "#0e1b18",
        "input-text-dark": "#ffffff",
        "input-placeholder-light": "#509589",
        "input-placeholder-dark": "#a0b8b4",
        
        // Goals page colors with Zaman brand colors
        "primary-goals": "#2D9A86",
        "secondary-goals": "#EEFE6D",
        "zaman-green": "#2D9A86",
        "zaman-solar": "#EEFE6D",
        "background-light-goals": "#f8fbfb",
        "background-dark-goals": "#101d1b",
        "surface-light": "#ffffff",
        "surface-dark": "#1a2c28",
        "text-light": "#0e1b18",
        "text-dark": "#e0e5e4",
        "subtle-light": "#509589",
        "subtle-dark": "#a0c7c0",
        "positive-light": "#2D9A86",
        "positive-dark": "#34d399",
        "negative-light": "#e72e08",
        "negative-dark": "#f87171"
      },
      backgroundImage: {
        'zaman-gradient': 'linear-gradient(135deg, #2D9A86 0%, #EEFE6D 100%)',
        'zaman-gradient-reverse': 'linear-gradient(135deg, #EEFE6D 0%, #2D9A86 100%)',
        'zaman-subtle': 'linear-gradient(135deg, #2D9A86 0%, #2D9A86 40%, #EEFE6D 100%)',
      },
      fontFamily: {
        "display": ["Inter", "sans-serif"]
      },
      borderRadius: {
        "DEFAULT": "0.5rem",
        "lg": "1rem",
        "xl": "1.5rem",
        "2xl": "2rem",
        "full": "9999px"
      },
      boxShadow: {
        'soft': '0 4px 12px 0 rgba(0,0,0,0.05)',
      }
    },
  },
  plugins: [],
}