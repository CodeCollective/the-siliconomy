import { defineConfig } from 'vite';
import glsl from 'vite-plugin-glsl';
import fs from 'node:fs';

const keyPath  = process.env.VITE_SSL_KEY  || '/certs/localhost-key.pem';
const certPath = process.env.VITE_SSL_CERT || '/certs/localhost-cert.pem';

export default defineConfig({
  plugins: [glsl()],
  server: {
    https: {
      key: fs.readFileSync(keyPath),
      cert: fs.readFileSync(certPath),
      // optional hardening; not strictly needed:
      minVersion: 'TLSv1.2'
    },
    host: true, // 0.0.0.0
    port: 5173
  },
  esbuild: {
    target: 'es2022',
    supported: { 'top-level-await': true }
  },
  build: { target: 'es2022' },
  optimizeDeps: {
    esbuildOptions: {
      target: 'es2022',
      supported: { 'top-level-await': true }
    }
  }
});
