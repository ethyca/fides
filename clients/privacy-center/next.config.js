const path = require("path");
const { version } = require("./package.json");

const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

// Transpile the modules needed for Swagger UI
const withTM = require("next-transpile-modules")([
  "react-syntax-highlighter",
  "swagger-client",
  "swagger-ui-react",
]);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // DEFER: This would be preferable, but requires Next 13 (see https://github.com/ethyca/fides/issues/3173)
  // transpilePackages: ["fides-js"],
  poweredByHeader: false,
  env: {
    version: "1.2.3",
  },
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
      {
        // Rewrite requests for "/fides-ext-gpp.js" to the /api/fides-ext-gpp-js route, to
        // provide a "virtual" static file download link
        source: "/:path(fides-ext-gpp.js)",
        destination: "/api/fides-ext-gpp-js",
      },
    ];
  },
};

module.exports = withTM(withBundleAnalyzer(nextConfig));
