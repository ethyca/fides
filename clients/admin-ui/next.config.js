const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

/** @type {import("next").NextConfig} */
const nextConfig = {
  // `reactStrictMode` must be false for Chakra v2 modals to behave properly. See https://github.com/chakra-ui/chakra-ui/issues/5321#issuecomment-1219327270
  reactStrictMode: false,
  experimental: {
    // Data flow scanning sometimes takes longer than the default of 30 seconds
    proxyTimeout: 120000,
  },
  transpilePackages: [
    "fidesui",
    /*
      Due to an issue with ant icons and next js 15, we need to transpile all ant-design packages.
      See
      - https://github.com/vercel/next.js/issues/65707
      - https://github.com/ant-design/ant-design/issues/46053#issuecomment-1905553667
    */
    "@ant-design",
    "@rc-component",
    "antd",
    "rc-cascader",
    "rc-checkbox",
    "rc-collapse",
    "rc-dialog",
    "rc-drawer",
    "rc-dropdown",
    "rc-field-form",
    "rc-image",
    "rc-input",
    "rc-input-number",
    "rc-mentions",
    "rc-menu",
    "rc-motion",
    "rc-notification",
    "rc-pagination",
    "rc-picker",
    "rc-progress",
    "rc-rate",
    "rc-resize-observer",
    "rc-segmented",
    "rc-select",
    "rc-slider",
    "rc-steps",
    "rc-switch",
    "rc-table",
    "rc-tabs",
    "rc-textarea",
    "rc-tooltip",
    "rc-tree",
    "rc-tree-select",
    "rc-upload",
    "rc-util",
  ],
  images: {
    loader: "custom",
  },
  async rewrites() {
    // The tests run without a server. Rewrites cause Next to continually try to connect,
    // which spams the logs with "ECONNREFUSED".
    if (process.env.NODE_ENV === "test") {
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

module.exports = withBundleAnalyzer(nextConfig);
