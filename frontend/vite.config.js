import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        // SSE 总结/问答可能等待较久，避免 dev 代理提前断开
        timeout: 600000,
        proxyTimeout: 600000,
      },
    },
  },
});
