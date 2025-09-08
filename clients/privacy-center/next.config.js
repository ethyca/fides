const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

const { importFidesPackageVersion } = require("../build-utils");

/** @type {import('next').NextConfig} */
const nextConfig = {
  // `reactStrictMode` must be false for Chakra v2 modals to behave properly. See https://github.com/chakra-ui/chakra-ui/issues/5321#issuecomment-1219327270
  reactStrictMode: false,
  poweredByHeader: false,
  env: {
    version: importFidesPackageVersion(),
  },
  transpilePackages: ["react-syntax-highlighter", "fidesui", "rc-utils"],

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
