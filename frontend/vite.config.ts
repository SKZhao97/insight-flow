import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/sources": "http://127.0.0.1:8000",
      "/documents": "http://127.0.0.1:8000",
      "/reports": "http://127.0.0.1:8000",
      "/workflow-runs": "http://127.0.0.1:8000",
      "/workflows": "http://127.0.0.1:8000"
    }
  }
});
