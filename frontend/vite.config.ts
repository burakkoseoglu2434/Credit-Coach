import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const api = "http://127.0.0.1:8000";
const proxy = { "/score": api, "/batch": api, "/health": api };

export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
});
