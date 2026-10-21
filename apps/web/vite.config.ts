import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@state': path.resolve(__dirname, './src/state'),
      '@api': path.resolve(__dirname, './src/api'),
      '@audio': path.resolve(__dirname, './src/audio'),
      '@stt': path.resolve(__dirname, './src/stt'),
      '@tts': path.resolve(__dirname, './src/tts'),
      '@i18n': path.resolve(__dirname, './src/i18n'),
      '@styles': path.resolve(__dirname, './src/styles'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8787',
      '/ws': {
        target: 'ws://localhost:8787',
        ws: true,
      },
    },
  },
});