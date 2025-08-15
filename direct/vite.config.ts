import { defineConfig } from 'vite';
import glsl from 'vite-plugin-glsl';
import fs from 'node:fs';
import path from 'node:path';

const keyPath  = process.env.VITE_SSL_KEY  || '/certs/localhost-key.pem';
const certPath = process.env.VITE_SSL_CERT || '/certs/localhost-cert.pem';

export default defineConfig({
  plugins: [glsl()],
  server: {
    https: { key: fs.readFileSync(keyPath), cert: fs.readFileSync(certPath), minVersion: 'TLSv1.2' },
    host: true,
    port: 5173
  },
  esbuild: {
    target: 'es2022',
    supported: { 'top-level-await': true }
  },
  build: { target: 'es2022' },

  // keep the dep-scanner from wandering into /three.js/examples/*.html
  optimizeDeps: {
    exclude: ['three'],
    entries: ['index.html', 'src/main.ts']  // point to YOUR app entry files
  },

  resolve: {
    alias: {
      three: path.resolve(__dirname, 'three.js'),                          // repo root
      'three/addons/': path.resolve(__dirname, 'three.js/examples/jsm/')   // ← key line
    },
    dedupe: ['three']
  }
});
