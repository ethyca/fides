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

/** @type {import('next').NextConfig} */
const nextConfig = {
  // `reactStrictMode` must be false for Chakra v2 modals to behave properly. See https://github.com/chakra-ui/chakra-ui/issues/5321#issuecomment-1219327270
  reactStrictMode: false,
  poweredByHeader: false,
  env: {
    version: "1.2.3",
  },
  transpilePackages: [
    "react-syntax-highlighter",
    "swagger-client",
    "swagger-ui-react",
    "fidesui",
  ],
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

module.exports = withBundleAnalyzer(nextConfig);
