import { defineConfig, loadEnv } from 'vite';
import solid from 'vite-plugin-solid';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const isProduction = mode === 'production';

  return {
    plugins: [
      solid(),
      VitePWA({
        registerType: 'autoUpdate',
        workbox: {
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/api\./,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'api-cache',
                expiration: {
                  maxEntries: 100,
                  maxAgeSeconds: 60 * 60 * 24, // 1 day
                },
              },
            },
          ],
        },
        manifest: {
          name: 'Omnitide Control Panel',
          short_name: 'Omnitide',
          description: 'Next-generation agent orchestration interface',
          theme_color: '#0f172a',
          background_color: '#0f172a',
          display: 'standalone',
          icons: [
            {
              src: 'pwa-192x192.png',
              sizes: '192x192',
              type: 'image/png',
            },
            {
              src: 'pwa-512x512.png',
              sizes: '512x512',
              type: 'image/png',
            },
          ],
        },
      }),
    ],

    // Path resolution
    resolve: {
      alias: {
        '@': '/src',
        '@/components': '/src/components',
        '@/services': '/src/services',
        '@/store': '/src/store',
        '@/types': '/src/types',
        '@/utils': '/src/utils',
      },
    },

    // Development server
    server: {
      host: true,
      port: 5173,
      strictPort: true,
      cors: true,
      hmr: {
        overlay: true,
      },
    },

    // Preview server
    preview: {
      host: true,
      port: 4173,
      strictPort: true,
    },

    // Build configuration
    build: {
      target: 'esnext',
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: !isProduction,
      minify: isProduction ? 'terser' : false,
      cssCodeSplit: true,

      // Rollup options
      rollupOptions: {
        onwarn(warning, warn) {
          // Suppress "this" keyword warnings in class methods
          if (warning.code === 'THIS_IS_UNDEFINED') return;
          warn(warning);
        },

        output: {
          // Manual chunk splitting for optimal loading
          manualChunks: {
            // Core framework
            vendor: ['solid-js'],

            // Visualization libraries
            visualization: ['pixi.js', 'd3'],

            // Utilities
            utils: ['protobufjs'],
          },

          // Asset naming
          chunkFileNames: isProduction
            ? 'assets/js/[name]-[hash].js'
            : 'assets/js/[name].js',
          entryFileNames: isProduction
            ? 'assets/js/[name]-[hash].js'
            : 'assets/js/[name].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name!.split('.');
            const ext = info[info.length - 1];
            if (/\.(png|jpe?g|gif|svg|webp|avif)$/i.test(assetInfo.name!)) {
              return `assets/images/[name]-[hash].${ext}`;
            }
            if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name!)) {
              return `assets/fonts/[name]-[hash].${ext}`;
            }
            return `assets/[ext]/[name]-[hash].${ext}`;
          },
        },
      },

      // Terser options for production
      terserOptions: isProduction
        ? {
            compress: {
              drop_console: true,
              drop_debugger: true,
              pure_funcs: ['console.log'],
            },
            mangle: {
              safari10: true,
            },
            format: {
              comments: false,
            },
          }
        : undefined,
    },

    // CSS configuration
    css: {
      devSourcemap: !isProduction,
      postcss: './postcss.config.cjs',
    },

    // Dependency optimization
    optimizeDeps: {
      include: ['solid-js', 'solid-js/web', 'd3', 'pixi.js'],
      exclude: ['@vite/client', '@vite/env'],
    },

    // Environment variables
    define: {
      __DEV__: JSON.stringify(!isProduction),
      __PROD__: JSON.stringify(isProduction),
      __VERSION__: JSON.stringify(process.env.npm_package_version),
    },
  };
});
