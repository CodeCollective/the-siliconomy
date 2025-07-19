import { defineConfig } from 'vite';
import fs from 'fs';
import path from 'path';
import wasm from 'vite-plugin-wasm';
import basicSsl from '@vitejs/plugin-basic-ssl';

// Create self-signed cert or use mkcert for real ones
const certDir = '../ssl';
const https = {
  key: fs.readFileSync(path.join(certDir, 'server.key')),
  cert: fs.readFileSync(path.join(certDir, 'server.crt')),
};

export default defineConfig({
  plugins: [
    wasm(),
    basicSsl()
  ],
  server: {
    port: 3443,
    https,
    host: '0.0.0.0', // required for network testing
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp'
    },
    fs: {
      // Allow serving files outside of the root
      allow: [
        "../.."
      ]
    }
  },
  optimizeDeps: {
    exclude: ['@babylonjs/havok']
  }
});
