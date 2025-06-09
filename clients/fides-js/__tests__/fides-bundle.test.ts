/**
 * Test to verify that the Fides bundle works in both IIFE and ESM formats.
 * Assumes that the bundles have already been built using `npm run build`.
 */
import fs from "fs";
import path from "path";

/**
 * Check if a file appears to be in IIFE format
 */
const isIIFEFormat = (content: string): boolean => {
  return (
    content.trim().startsWith("(function") ||
    content.includes("window.Fides") ||
    content.includes("var Fides")
  );
};

/**
 * Check if a file appears to be in ES Module format
 */
const isESMFormat = (content: string): boolean => {
  return (
    content.includes("export") ||
    content.includes("import") ||
    !content.includes("var Fides = ")
  );
};

/**
 * Check if a file does not contain AMD module checks
 */
const hasNoAMDChecks = (content: string): boolean => {
  return !content.includes("define.amd");
};

/**
 * Check if a file preserves existing globals (uses extend: true)
 */
const usesExtendOption = (content: string): boolean => {
  // Look for patterns that indicate the extend option is being used
  return (
    content.includes("Object.assign") ||
    content.includes("= window.Fides || {}") ||
    content.includes("= globalThis.Fides || {}")
  );
};

/**
 * Helper function to validate bundle existence and format
 */
const validateBundle = (fileName: string, format: "iife" | "esm"): void => {
  const distDir = path.join(process.cwd(), "dist");
  const filePath = path.join(distDir, fileName);

  expect(fs.existsSync(filePath)).toBe(true);

  const content = fs.readFileSync(filePath, "utf8");

  if (format === "iife") {
    expect(isIIFEFormat(content)).toBe(true);
    expect(hasNoAMDChecks(content)).toBe(true);
    expect(usesExtendOption(content)).toBe(true);
  } else if (format === "esm") {
    expect(isESMFormat(content)).toBe(true);
  }
};

const iifeBundles = ["fides.js", "fides-tcf.js", "fides-headless.js"];

const esmBundles = [
  "fides.mjs",
  "fides-tcf.mjs",
  "fides-headless.mjs",
  "fides-ext-gpp.mjs",
];

/**
 * Check that all required bundles exist before running tests
 */
const checkBundlesExist = (): void => {
  const distDir = path.join(process.cwd(), "dist");
  const allBundles = [...iifeBundles, ...esmBundles];
  const missingBundles: string[] = [];

  // Check if dist directory exists
  if (!fs.existsSync(distDir)) {
    throw new Error(
      `❌ Build directory not found: ${distDir}\n` +
        `Please run 'npm run build' to generate the bundles before running these tests.`,
    );
  }

  // Check each bundle file
  allBundles.forEach((fileName) => {
    const filePath = path.join(distDir, fileName);
    if (!fs.existsSync(filePath)) {
      missingBundles.push(fileName);
    }
  });

  if (missingBundles.length > 0) {
    throw new Error(
      `❌ Missing bundle files: ${missingBundles.join(", ")}\n` +
        `Please run 'npm run build' to generate all bundles before running these tests.\n` +
        `Expected bundles: ${allBundles.join(", ")}`,
    );
  }
};

describe("Fides Bundle Tests", () => {
  beforeAll(() => {
    try {
      checkBundlesExist();
    } catch (error) {
      // Re-throw with additional context
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      throw new Error(`Bundle validation failed: ${errorMessage}`);
    }
  });

  describe("IIFE Browser Format", () => {
    iifeBundles.forEach((fileName) => {
      it(`should generate valid IIFE format for ${fileName}`, () => {
        validateBundle(fileName, "iife");
      });
    });
  });

  describe("ES Module Format", () => {
    esmBundles.forEach((fileName) => {
      it(`should generate valid ESM format for ${fileName}`, () => {
        validateBundle(fileName, "esm");
      });
    });
  });
});
