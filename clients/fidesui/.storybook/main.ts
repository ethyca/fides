import { createRequire } from "module";
import { dirname, join } from "path";

import type { StorybookConfig } from "@storybook/react-vite";

const require = createRequire(import.meta.url);
const config: StorybookConfig = {
  refs: {
    "@chakra-ui/react": {
      disable: true,
    },
  },
  stories: ["../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"],
  addons: [],
  framework: {
    name: "@storybook/react-vite",
    options: {
      legacyRootApi: true,
    },
  },
  async viteFinal(config) {
    // Merge custom configuration into the default config
    const { mergeConfig } = await import("vite");

    // Resolve the CJS entry for @chakra-ui/react because the ESM distribution
    // (dist/esm/index.mjs) has broken relative imports referencing non-existent files.
    const chakraCjsEntry = join(
      dirname(require.resolve("@chakra-ui/react/package.json")),
      "dist/cjs/index.cjs",
    );

    return mergeConfig(config, {
      plugins: [],
      esbuild: { jsx: "automatic" },
      resolve: {
        alias: {
          "@chakra-ui/react": chakraCjsEntry,
        },
      },
      optimizeDeps: {
        // Mark msw as external during dep pre-bundling. The msw imports in
        // @vitest/mocker (bundled with Storybook) are optional dynamic imports
        // that only execute when msw is actively used for browser mocking.
        esbuildOptions: {
          external: ["msw", "msw/browser", "msw/core/http"],
        },
      },
    });
  },
};
export default config;
