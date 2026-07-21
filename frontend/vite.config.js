import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  // Keep module resolution inside the project path. This avoids Windows/OneDrive
  // real-path traversal failures while preserving normal behavior elsewhere.
  resolve: { preserveSymlinks: true },
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'charts', test: /node_modules[\\/](chart\.js|react-chartjs-2)/, priority: 30 },
            { name: 'maps', test: /node_modules[\\/](leaflet|react-leaflet)/, priority: 30 },
            { name: 'motion', test: /node_modules[\\/]framer-motion/, priority: 30 },
            { name: 'react', test: /node_modules[\\/](react|react-dom)/, priority: 20 },
            { name: 'vendor', test: /node_modules/, priority: 10, maxSize: 300000 },
          ],
        },
      },
    },
  },
});
