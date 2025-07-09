const fs = require("fs");

/**
 * Imports and validates the Fides package version from a JSON file
 * @param {string} path - Path to the version.json file, defaults to "./version.json"
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
    const versionJson = JSON.parse(fs.readFileSync(path, "utf-8"));

    // Validate version file structure and content
    if (
      !versionJson?.version ||
      typeof versionJson.version !== "string" ||
      versionJson.version.trim() === ""
    ) {
      console.warn(
        `WARNING: Importing Fides package version failed! Invalid version file format or missing version in ${path}`
      );
      return errorVersion;
    }

    return versionJson.version.trim();
  } catch (error) {
    console.warn(
      `WARNING: Importing Fides package version failed! Error when importing version file from ${path}:`,
      error
    );
    return errorVersion;
  }
};

// Support both CommonJS and ES module imports
module.exports = {
  importFidesPackageVersion,
};

// Also export as named export for ES modules
module.exports.importFidesPackageVersion = importFidesPackageVersion;
