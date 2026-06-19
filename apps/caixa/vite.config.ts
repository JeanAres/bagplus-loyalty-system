/// <reference types="node" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@bagplus/shared/api': fileURLToPath(new URL('../shared/api/index.ts', import.meta.url)),
      '@bagplus/shared/types': fileURLToPath(new URL('../shared/types/index.ts', import.meta.url)),
      '@bagplus/shared/utils': fileURLToPath(new URL('../shared/utils/index.ts', import.meta.url)),
      '@bagplus/shared/hooks': fileURLToPath(new URL('../shared/hooks/index.ts', import.meta.url)),
      '@bagplus/shared/components': fileURLToPath(new URL('../shared/components/index.ts', import.meta.url)),
      '@bagplus/shared': fileURLToPath(new URL('../shared/index.ts', import.meta.url)),
    }
  }
})