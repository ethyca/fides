const isDebugMode = process.env.FIDES_PRIVACY_CENTER__DEBUG === "true";
const debugMarker = "=>";
globalThis.fidesDebugger = isDebugMode
  ? (...args) => console.log(`\x1b[33m${debugMarker}\x1b[0m`, ...args)
  : () => {};
globalThis.fidesError = isDebugMode
  ? (...args) => console.log(`\x1b[31m${debugMarker}\x1b[0m`, ...args)
  : () => {};

const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

// DEFER (PROD-1981): Replace with `transpilePackages` after upgrading to 13.0.0
// Transpile the modules needed for Swagger UI
const withTM = require("next-transpile-modules")([
  "react-syntax-highlighter",
  "swagger-client",
  "swagger-ui-react",
  "fidesui",
]);

/** @type {import('next').NextConfig} */
const nextConfig = {
  // `reactStrictMode` must be false for Chakra v2 modals to behave properly. See https://github.com/chakra-ui/chakra-ui/issues/5321#issuecomment-1219327270
  reactStrictMode: false,
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
