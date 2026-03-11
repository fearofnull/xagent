import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import viteCompression from 'vite-plugin-compression'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // Gzip compression
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240, // Only compress files larger than 10KB
      algorithm: 'gzip',
      ext: '.gz',
      deleteOriginFile: false
    }),
    // Brotli compression (better compression ratio)
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240,
      algorithm: 'brotliCompress',
      ext: '.br',
      deleteOriginFile: false
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // Optimize dependencies
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios', 'element-plus'],
    exclude: []
  },
  // Performance optimizations
  esbuild: {
    drop: ['console', 'debugger'], // Remove console and debugger in production
    legalComments: 'none'
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    },
    // Enable HTTP/2 for better performance
    https: false,
    // Optimize HMR
    hmr: {
      overlay: true
    }
  },
  build: {
    // Output to ../src/xagent/web_admin/static for Flask to serve
    outDir: '../src/xagent/web_admin/static',
    // Clean output directory before build
    emptyOutDir: true,
    // Generate source maps for debugging
    sourcemap: false,
    // Optimize build with esbuild (faster than terser)
    minify: 'esbuild',
    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
    // Target modern browsers for smaller bundle size
    target: 'es2015',
    // CSS code splitting
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'element-plus': ['element-plus'],
          'element-icons': ['@element-plus/icons-vue']
        },
        // Asset file naming with hash for cache busting
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name)) {
            return `assets/images/[name]-[hash][extname]`
          } else if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
            return `assets/fonts/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        },
        // JS chunk naming with hash
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js'
      }
    },
    // Compression settings
    reportCompressedSize: true,
    // Optimize dependencies
    commonjsOptions: {
      transformMixedEsModules: true
    }
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: './tests/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      include: ['src/**/*.{js,vue}'],
      exclude: [
        'src/main.js',
        'src/**/*.spec.js',
        'src/**/*.test.js'
      ],
      all: true,
      lines: 70,
      functions: 70,
      branches: 70,
      statements: 70
    }
  }
})
