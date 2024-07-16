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
    /**
     * Data flow scanning sometimes takes longer than the default of 30 seconds
     */
    proxyTimeout: 120000,
  },
  images: {
    loader: "custom",
  },
};

module.exports = withTM(withBundleAnalyzer(nextConfig));
