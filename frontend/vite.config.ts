import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Static-demo builds are served from an arbitrary sub-path, so assets must be relative.
  base: process.env.VITE_STATIC_DEMO === 'true' ? './' : '/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/analyze': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/jobs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/results': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/samples': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
