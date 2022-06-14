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
    // these paths are unnecessarily complicated due to our backend being
    // picky about trailing slashes https://github.com/ethyca/fides/issues/690
    return [
      {
        source: `/api/v1/:path`,
        destination: "http://fidesctl:8080/api/v1/:path/",
      },
      {
        source: `/api/v1/:first/:second*`,
        destination: "http://fidesctl:8080/api/v1/:first/:second*",
      },
    ];
  },
};

module.exports = withBundleAnalyzer(nextConfig);
