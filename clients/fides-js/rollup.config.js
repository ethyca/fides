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
  const isV1ConsentConfig = typeof privacyCenterConfig.consent?.button === "undefined";
  const privacyCenterOptions = isV1ConsentConfig ? privacyCenterConfig.consent?.consentOptions : privacyCenterConfig.consent?.page.consentOptions;

  if (privacyCenterOptions.length === 0) {
    console.warn(
      "Privacy Center config.json has no consent options configured."
    );
  }

  const options = privacyCenterOptions.map((pcOption) => ({
    fidesDataUseKey: pcOption.fidesDataUseKey,
    default: pcOption.default,
    cookieKeys: pcOption.cookieKeys,
  }));

  /**
   * @type {import('./src/lib/consent-config').ConsentConfig}
   */
  const consentConfig = {
    options,
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
