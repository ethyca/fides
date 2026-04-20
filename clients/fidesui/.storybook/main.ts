import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  refs: {
    "@chakra-ui/react": {
      disable: true,
    },
  },
  stories: ["../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"],
  addons: ["@storybook/addon-a11y"],
  framework: {
    name: "@storybook/react-vite",
    options: {},
  },
  async viteFinal(config) {
    // Merge custom configuration into the default config
    const { mergeConfig } = await import("vite");

    return mergeConfig(config, {
      plugins: [],
      esbuild: { jsx: "automatic" },
      resolve: {
        alias: [
          // Route antd/lib/* deep imports to the ESM build (antd/es/*).
          // Prevents two separate antd instances (CJS lib + ESM es) from coexisting in
          // Vite's module graph, which would break ConfigProvider-based theming.
          { find: /^antd\/lib\/(.+)$/, replacement: "antd/es/$1" },
          { find: "antd/lib", replacement: "antd/es" },
        ],
      },
    });
  },
};

export default config;
