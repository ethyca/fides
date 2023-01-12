const path = require("path");
const privacyCenterConfig = require("./config/config.json");

/** @type {import('next').NextConfig} */
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

/**
 * We can catch business logic problems with the supplied config.json here.
 *
 * Typescript errors will be caught by the initial instantiation of the config object.
 */
const configIsValid = () => {
  // Cannot currently have more than one consent be executable
  if (privacyCenterConfig.consent) {
    const executables = privacyCenterConfig.consent.consentOptions.filter(
      (option) => option.executable
    );
    if (executables.length > 1) {
      return {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      };
    }
  }
  return { isValid: true };
};

// Check that our config.json is valid
const { isValid, message } = configIsValid();
if (!isValid) {
  // Throw a red warning
  console.error(
    "\x1b[31m%s",
    `Error with privacy center configuration: ${message}`
  );
  throw "Privacy center config invalid. Please fix, then rerun the application.";
}

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
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
};

module.exports = withBundleAnalyzer(nextConfig);
