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
        // note: we may need to be careful about this in the future
        // our backend paths are picky about trailing slashes, and
        // nextjs automatically removes trailing slashes. may have to
        // be careful when there are query parameters.
        destination: "http://0.0.0.0:8080/api/v1/:path*/",
      },
    ];
  },
};

module.exports = withBundleAnalyzer(nextConfig);
