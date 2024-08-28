const path = require("path");

const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

// DEFER (PROD-1981): Replace with `transpilePackages` after upgrading to 13.0.0
const withTM = require("next-transpile-modules")(["fidesui"]);

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

module.exports = withTM(withBundleAnalyzer(nextConfig));
