/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    // Use https://hatscripts.github.io/circle-flags/ as a repository of nicely
    // formatted SVG flags. NOTE: this works well as a sample app, but having a
    // github.io (GitHub Pages) CDN totally works, although they don't *really*
    // encourage it!
    remotePatterns: [
      {
        protocol: "https",
        hostname: "hatscripts.github.io",
        pathname: "/circle-flags/**",
      },
    ],
  },
};

module.exports = nextConfig;
