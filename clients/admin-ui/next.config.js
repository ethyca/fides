const path = require("path");

const withBundleAnalyzer = require("@next/bundle-analyzer")({
    enabled: process.env.ANALYZE === "true",
});

/** @type {import("next").NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    experimental: {
        /**
         * Data flow scanning sometimes takes longer than the default of 30 seconds
         */
        proxyTimeout: 120000
    },
    async rewrites() {
        // The tests run without a server. Rewrites cause Next to continually try to connect,
        // which spams the logs with "ECONNREFUSED".
        if (process.env.NODE_ENV === "test") {
            return [];
        }

        // these paths are unnecessarily complicated due to our backend being
        // picky about trailing slashes https://github.com/ethyca/fides/issues/690
        return [
            {
                source: `/api/v1/:path`,
                destination: `${process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER}/api/v1/:path/`,
            },
            {
                source: `/api/v1/:first/:second*`,
                destination: `${process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER}/api/v1/:first/:second*`,
            },
            // The /health path does not live under /api/v1
            {
                source: `/health`,
                destination: `${process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER}/health`
            }
        ]
    },
    images: {
        loader: "custom",
    },
};

module.exports = withBundleAnalyzer(nextConfig);
