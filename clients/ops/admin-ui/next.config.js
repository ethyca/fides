const path = require('path');

/** @type {import('next').NextConfig} */
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig = {
  reactStrictMode: true,
  webpack(config) {
    Object.assign(config.resolve.alias, {
      react: path.resolve(__dirname, 'node_modules', 'react'),
      'react-dom': path.resolve(__dirname, 'node_modules', 'react-dom'),
      '@emotion/react': path.resolve(
        __dirname,
        'node_modules',
        '@emotion/react'
      ),
    });

    return config;
  },
  images: {
    loader: 'custom',
  },
};

module.exports = withBundleAnalyzer(nextConfig);
