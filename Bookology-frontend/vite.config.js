import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: false,
    target: 'es2019',
    cssCodeSplit: true,
    chunkSizeWarningLimit: 250,
    brotliSize: true,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          vendor: ['@tanstack/react-query'],
          editor: ['@tiptap/react', '@tiptap/starter-kit', '@tiptap/extension-placeholder']
        }
      }
    }
  },
})
