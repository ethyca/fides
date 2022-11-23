const path = require("path");

const withBundleAnalyzer = require("@next/bundle-analyzer")({
    enabled: process.env.ANALYZE === "true",
});

/** @type {import("next").NextConfig} */
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
    experimental: {
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
        ]
    },
    images: {
        loader: "custom",
    },
};

module.exports = withBundleAnalyzer(nextConfig);
