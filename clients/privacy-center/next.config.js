const isDebugMode = process.env.FIDES_PRIVACY_CENTER__DEBUG === "true";
const debugMarker = "=>";
globalThis.fidesDebugger = isDebugMode
  ? (...args) => console.log(`\x1b[33m${debugMarker}\x1b[0m`, ...args)
  : () => {};
globalThis.fidesError = isDebugMode
  ? (...args) => console.log(`\x1b[31m${debugMarker}\x1b[0m`, ...args)
  : () => {};

const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

/**
 * Imports and validates the Fides package version from a JSON file
 * @param {string} path - Path to the version.json file, defaults to "../version.json"
 * @returns {string} The package version string, or "unknown" if version cannot be determined
 * @example
 * // version.json
 * {
 *   "version": "1.2.3"
 * }
 *
 * importFidesPackageVersion() // Returns "1.2.3"
 * importFidesPackageVersion("invalid/path") // Returns "unknown"
 */
const importFidesPackageVersion = (path = "../version.json") => {
  const errorVersion = "unknown";
  try {
    const versionJson = require(path);

    // Validate version file structure and content
    if (
      !versionJson?.version ||
      typeof versionJson.version !== "string" ||
      versionJson.version.trim() === ""
    ) {
      console.warn(
        `WARNING: Importing Fides package version failed! Invalid version file format or missing version in ${path}`,
      );
      return errorVersion;
    }

    return versionJson.version.trim();
  } catch (error) {
    console.warn(
      `WARNING: Importing Fides package version failed! Error when importing version file from ${path}:`,
      error,
    );
    return errorVersion;
  }
};

/** @type {import('next').NextConfig} */
const nextConfig = {
  // `reactStrictMode` must be false for Chakra v2 modals to behave properly. See https://github.com/chakra-ui/chakra-ui/issues/5321#issuecomment-1219327270
  reactStrictMode: false,
  poweredByHeader: false,
  env: {
    version: importFidesPackageVersion(),
  },
  transpilePackages: ["react-syntax-highlighter", "fidesui"],

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
