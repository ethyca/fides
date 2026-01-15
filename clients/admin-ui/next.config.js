const path = require("path");
const webpack = require("webpack");

const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

// DEFER (PROD-1981): Replace with `transpilePackages` after upgrading to 13.0.0
// rc-util is required for Ant Design components (Collapse, Drawer, etc.) to work properly
// @ant-design/x and antd need to be transpiled to resolve ES module import issues
const withTM = require("next-transpile-modules")(["fidesui", "rc-util", "@ant-design/x", "antd"]);

/** @type {import("next").NextConfig} */
const nextConfig = {
  // `reactStrictMode` must be false for Chakra v2 modals to behave properly. See https://github.com/chakra-ui/chakra-ui/issues/5321#issuecomment-1219327270
  reactStrictMode: false,
  experimental: {
    // Data flow scanning sometimes takes longer than the default of 30 seconds
    proxyTimeout: 120000,
  },
  images: {
    loader: "custom",
  },
  webpack: (config, { isServer }) => {
    // Handle ESM packages used by @ant-design/x
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }

    // Fix antd version import issue - alias to point to index.js which exports the version
    if (!config.resolve.alias) {
      config.resolve.alias = {};
    }
    config.resolve.alias["antd/es/version"] = path.resolve(__dirname, "node_modules/antd/es/version/index.js");

    // Handle ESM externals for react-syntax-highlighter used by @ant-design/x
    // Ignore the problematic async language loader that tries to import ESM packages
    config.plugins.push(
      new webpack.IgnorePlugin({
        resourceRegExp: /^refractor\/.*$/,
        contextRegExp: /react-syntax-highlighter/,
      })
    );

    return config;
  },
  async rewrites() {
    // The CI tests run without a server, so we leave this value out of .env.test.
    // These rewrites then cause Next to continually try to connect, which spams the logs with "ECONNREFUSED".
    // Use npm run cy:start:dev to run the tests with a server during local development.
    if (!process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER) {
      return [];
    }
    // Proxy all requests to the API server during local development
    return [
      {
        source: `/api/v1/:path`,
        destination: `${process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER}/api/v1/:path`,
      },
      {
        source: `/api/v1/:first/:second*`,
        destination: `${process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER}/api/v1/:first/:second*`,
      },
      // V3 API proxying for consent sandbox
      {
        source: `/api/v3/:path`,
        destination: `${process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER}/api/v3/:path`,
      },
      {
        source: `/api/v3/:first/:second*`,
        destination: `${process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER}/api/v3/:first/:second*`,
      },
      // The /health path does not live under /api/v1
      {
        source: `/health`,
        destination: `${process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER}/health`,
      },
    ];
  },
};

// Export the static site for production.
// Rewrites are not supported in static sites.
if (process.env.PROD_EXPORT === "true") {
  delete nextConfig.rewrites;
  nextConfig.output = "export";
}

module.exports = withTM(withBundleAnalyzer(nextConfig));
