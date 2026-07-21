/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Light "analytics console" surfaces (validated reference palette).
        plane: "#f3f4f1", // page background
        surface: "#ffffff", // cards
        line: "#e4e3dd", // hairline borders
        accent: {
          DEFAULT: "#2a78d6",
          600: "#1c5cab",
          soft: "#eaf1fb",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(11,11,11,0.04), 0 1px 3px rgba(11,11,11,0.06)",
      },
    },
  },
  plugins: [],
};
