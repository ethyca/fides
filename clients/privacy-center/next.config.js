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
  webpack(config) {
    return config;
  },
};

module.exports = withBundleAnalyzer(nextConfig);
