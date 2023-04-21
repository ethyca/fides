const path = require("path");
const { validateConfig } = require("./scripts/validate-config.js");

validateConfig();

/** @type {import('next').NextConfig} */
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  webpack: (config, { isServer }) => {
    // Provide an empty fallback for the "fs" module for the client-side bundle
    // This is needed to ensure the dynamic import("fs") in loadConfigFromFile()
    // doesn't attempt to import the "fs" module when the client code runs!
    if (!isServer) {
      config.resolve.fallback.fs = false;
    }
    return config;
  },
  async rewrites() {
    return [
      {
        // Rewrite requests for "/fides.js" to the /api/fides-js route, to
        // provide a "virtual" static file download link
        // NOTE: also match "/fides-consent.js" for backwards compatibility
        source: "/:path(fides-consent.js|fides.js)",
        destination: "/api/fides-js",
      },
    ]
  },
};

module.exports = withBundleAnalyzer(nextConfig);
