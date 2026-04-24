const path = require("path");

const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

/** @type {import("next").NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Clients monorepo root. Explicit so Next 16 doesn't walk up to the fides
  // repo root (which has an unrelated package-lock.json) for file tracing.
  outputFileTracingRoot: path.join(__dirname, ".."),
  transpilePackages: ["fidesui", "@rc-component/util"],
  experimental: {
    // Data flow scanning sometimes takes longer than the default of 30 seconds
    proxyTimeout: 120000,
  },
  images: {
    loader: "custom",
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

module.exports = withBundleAnalyzer(nextConfig);
