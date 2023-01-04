import fs from "fs";
import path from "path";

import copy from "rollup-plugin-copy";
import dts from "rollup-plugin-dts";
import esbuild from "rollup-plugin-esbuild";
import nodeResolve from "@rollup/plugin-node-resolve";
import json from "@rollup/plugin-json";

const name = require("./package.json").name;
const isDev = process.env.NODE_ENV === "development";

/**
 * A subset of the Privacy Center's configuration is made available to `fides-consent.js` via
 * `consent-config.json`. This config file is generated at build time by this function.
 */
const generateConsentConfig = () => {
  console.log(
    `Updating "consent-config.json" with Privacy Center configuration.`
  );

  /**
   * @type {import('../../types/config').Config}
   */
  const privacyCenterConfig = require("../../config/config.json");
  const consentOptions = privacyCenterConfig.consent?.consentOptions ?? [];

  if (consentOptions.length === 0) {
    console.warn(
      "Privacy Center config.json has no consent options configured."
    );
  }

  /**
   * @type {import('./src/lib/cookie').CookieKeyConsent}
   */
  const defaults = {};
  consentOptions.forEach(({ cookieKeys, default: current }) => {
    if (current === undefined) {
      return;
    }

    cookieKeys.forEach((cookieKey) => {
      const previous = defaults[cookieKey];
      if (previous === undefined) {
        defaults[cookieKey] = current;
        return;
      }

      if (current !== previous) {
        console.warn(`Conflicting configuration for cookieKey "${cookieKey}".`);
      }

      defaults[cookieKey] = previous && current;
    });
  });

  const consentConfig = {
    defaults: defaults,
  };

  fs.writeFileSync(
    path.resolve("./src/consent-config.json"),
    JSON.stringify(consentConfig, null, 2)
  );
};

generateConsentConfig();

/**
 * @type {import('rollup').RollupOptions}
 */
export default [
  {
    input: `src/${name}.ts`,
    plugins: [
      nodeResolve(),
      json(),
      esbuild({
        minify: !isDev,
      }),
      copy({
        // Automatically add the built script to the privacy center's static files for testing:
        targets: [{ src: `dist/${name}.js`, dest: "../../public/" }],
        verbose: true,
        hook: "writeBundle",
      }),
    ],
    output: [
      {
        // Intended for browser <script> tag - defines `Fides` global. Also supports UMD loaders.
        file: `dist/${name}.js`,
        name: "Fides",
        format: "umd",
        sourcemap: isDev,
      },
    ],
  },
  {
    input: `src/lib/index.ts`,
    plugins: [nodeResolve(), esbuild()],
    output: [
      {
        // Compatible with ES module imports. Apps in this repo may be able to share the code.
        file: `dist/${name}.mjs`,
        format: "es",
        sourcemap: true,
      },
    ],
  },
  {
    input: `src/lib/index.ts`,
    plugins: [dts()],
    output: [
      {
        file: `dist/${name}.d.ts`,
      },
    ],
  },
];
