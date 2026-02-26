import type { StorybookConfig } from "@storybook/react-vite";

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
      // @chakra-ui/react@2.10.6 has an incomplete ESM distribution — several
      // internal .mjs files referenced by the package are missing from dist/esm/
      // (e.g. toast.store.mjs, transition-utils.mjs, use-style-config.mjs).
      // Forcing Vite to pre-bundle Chakra causes esbuild to use the complete CJS
      // build and produce a single ESM bundle, bypassing the broken imports.
      optimizeDeps: {
        include: ["@chakra-ui/react", "@chakra-ui/icons", "antd"],
      },
    });
  },
};
export default config;
