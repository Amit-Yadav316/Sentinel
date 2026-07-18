import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Backend runs on :8000. Proxy API + websocket so the frontend can use
// relative paths and stay origin-agnostic.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
      "/risk/stream": { target: "ws://localhost:8000", ws: true },
    },
  },
});
