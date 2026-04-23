import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      {
        find: '@agent-skills-dashboard/react/styles',
        replacement: path.resolve(
          __dirname,
          './node_modules/agent-skills-dashboard/packages/react/src/styles.css'
        ),
      },
      {
        find: '@agent-skills-dashboard/react',
        replacement: path.resolve(
          __dirname,
          './node_modules/agent-skills-dashboard/packages/react/src/index.ts'
        ),
      },
      {
        find: '@agent-skills-dashboard/core',
        replacement: path.resolve(__dirname, './src/lib/agentSkillsCore.ts'),
      },
      { find: '@', replacement: path.resolve(__dirname, './src') },
      { find: '@components', replacement: path.resolve(__dirname, './src/components') },
      { find: '@pages', replacement: path.resolve(__dirname, './src/pages') },
      { find: '@hooks', replacement: path.resolve(__dirname, './src/hooks') },
      { find: '@services', replacement: path.resolve(__dirname, './src/services') },
      { find: '@utils', replacement: path.resolve(__dirname, './src/utils') },
      { find: '@types', replacement: path.resolve(__dirname, './src/types') },
    ],
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: [],
  },
})
