/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#0a0e17",
          800: "#0f1523",
          700: "#161d2e",
          600: "#1e2740",
          500: "#2a3352",
        },
        accent: "#38bdf8",
        risk: {
          low: "#22c55e",
          mid: "#eab308",
          high: "#f97316",
          crit: "#ef4444",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
