import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  // Keep module resolution inside the project path. This avoids Windows/OneDrive
  // real-path traversal failures while preserving normal behavior elsewhere.
  resolve: { preserveSymlinks: true },
});
