const path = require("path");

/** @type {import('next').NextConfig} */
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig = {
  reactStrictMode: true,
  webpack(config) {
    Object.assign(config.resolve.alias, {
      react: path.resolve(__dirname, "node_modules", "react"),
      "react-dom": path.resolve(__dirname, "node_modules", "react-dom"),
      "@emotion/react": path.resolve(
        __dirname,
        "node_modules",
        "@emotion/react"
      ),
    });

    return config;
  },
  async rewrites() {
    return [
      {
        source: `/api/v1/:path*`,
        destination: "http://0.0.0.0:8080/api/v1/:path*/",
      },
    ];
  },
};

module.exports = withBundleAnalyzer(nextConfig);
